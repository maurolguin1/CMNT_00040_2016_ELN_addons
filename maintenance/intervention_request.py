# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from openerp.osv import osv, fields
from datetime import datetime, date
from openerp.tools.translate import _


class intervention_request(osv.osv):
    _name = "intervention.request"
    _inherit = ['mail.thread']

    def _get_ttr(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        for intervention in self.browse(cr, uid, ids, context=context):
            if not intervention.maintenance_type_id:
                continue
            if intervention.maintenance_type_id.type != 'correctivo':
                continue
            # Time to repair (TTR)
            create_date = datetime.strptime(intervention.fecha_solicitud, '%Y-%m-%d %H:%M:%S')
            final_date = intervention.work_order_ids.mapped('final_date')
            date_finished = final_date and all(final_date) and datetime.strptime(max(final_date), '%Y-%m-%d %H:%M:%S')
            if date_finished and create_date:
                ttr = date_finished - create_date
                ttr = ttr and round(ttr.total_seconds() / 3600, 2) or 0.0
            else:
                ttr = 0.0
            res[intervention.id] = ttr
        return res

    def _get_tbf(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        for intervention in self.browse(cr, uid, ids, context=context):
            if not intervention.maintenance_type_id:
                continue
            if intervention.maintenance_type_id.type != 'correctivo':
                continue
            # Time between fails (TBF)
            create_date = datetime.strptime(intervention.fecha_solicitud, '%Y-%m-%d %H:%M:%S')
            domain = [('maintenance_type_id.type', '=', 'correctivo'),
                      ('fecha_solicitud', '>', intervention.fecha_solicitud),
                      ('id', '!=', intervention.id)]
            next_maintenance = self.search(cr, uid, domain, order='fecha_solicitud', limit=1)
            if next_maintenance:
                intervention2 = self.pool.get('intervention.request').browse(cr, uid, next_maintenance, context=context)
                date_finished = datetime.strptime(intervention2.fecha_solicitud, '%Y-%m-%d %H:%M:%S')
                if date_finished and create_date:
                    tbf = date_finished - create_date
                    tbf = tbf and round(tbf.total_seconds() / 3600, 2) or 0.0
                else:
                    tbf = 0.0
            else:
                tbf = 0.0
            res[intervention.id] = tbf
        return res

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True, select=1, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}),
        'maintenance_type_id': fields.many2one('maintenance.type', 'maintenance type', required=False),
        'name': fields.char('Nombre', size=64, required=True, readonly=False),
        'solicitante_id': fields.many2one('res.users', 'Applicant', required=True),
        'element_ids': fields.many2one('maintenance.element', 'Maintenance elements'),
        'department_id': fields.many2one('hr.department', 'Department', required=False),
        'fecha_estimada': fields.datetime('Estimated date'),
        'motivo_cancelacion': fields.text('Reason for cancellation'),
        'fecha_solicitud': fields.datetime('Request date', required=True),
        'instrucciones': fields.text('Instructions'),
        'state':fields.selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
            ], 'State', select=True, readonly=False),
        'note': fields.text('Notes'),
        'deteccion': fields.text('Detection'),
        'sintoma': fields.text('Sign'),
        'efecto': fields.text('effect'),
        'work_order_ids': fields.one2many('work.order', 'request_id', 'Work Order', required=False, readonly=True),
        'ttr': fields.function(_get_ttr, type="float", string="TTR", readonly=True, help='Time to repair in hours', group_operator='avg'),
        'tbf': fields.function(_get_tbf, type="float", string="TBF", readonly=True, help='Time between fails in hours', group_operator='avg'),
        'type': fields.related('maintenance_type_id', 'type',
            type='selection',
            selection=[('gama', 'gamma'), ('correctivo', 'correctivo'), ('legal', 'legal'), ('preventivo', 'preventivo')],
            string='Type', readonly=True, store=True),
    }
    _defaults = {
        'state': 'draft',
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'intervention.request'),
        'fecha_solicitud': datetime.today(),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'intervention.request', context=c),
        'solicitante_id': lambda obj, cr, uid, context: uid,
    }
    _order = "fecha_solicitud asc"
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'intervention.request'),
        })
        return super(intervention_request, self).copy(cr, uid, id, default, context)
    
    def cancel(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if not ids:
            return False
        wizard_id = self.pool.get('cancel.intervention.request.wizard').create(cr, uid, {'intervention_request_id': ids[0]}, context)
        return {
            'name':"Cancelar solicitud",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'cancel.intervention.request.wizard',
            'res_id': wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }

    def confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'confirmed'})
        return True

    def open_work_order(self, cr, uid, order_id, context=None):
        data_pool = self.pool.get('ir.model.data')
        if not context:
            context = {} 
        if order_id:
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'maintenance', "action_work_order_tree")
        action_pool = self.pool.get(action_model)
        action = action_pool.read(cr, uid, action_id, context=context)
        action['domain'] = "[('id','=', "+str(order_id)+")]"
        return action
    
    def create_work_order(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        intervention_requests = self.pool.get('intervention.request').browse(cr, uid, ids, context)
        for intervention in intervention_requests:
            if intervention.maintenance_type_id:
                survey = intervention.maintenance_type_id.survey_id.id
            else:
                survey = None
            vals_order = {
                      'request_id':intervention.id,
                      'elements_ids' : intervention.element_ids and [(6, 0, [intervention.element_ids.id])] or False,
                      'origin_department_id': intervention.department_id.id,
                      'instrucciones': intervention.instrucciones,
                      'maintenance_type_id': intervention.maintenance_type_id.id,
                      'survey_id': survey,
                      'deteccion': intervention.deteccion,
                      'sintoma': intervention.sintoma,
                      'efecto': intervention.efecto,
                      'company_id': intervention.company_id.id,
                      'fecha': intervention.fecha_solicitud,
            }
            order_id = self.pool.get('work.order').create(cr, uid, vals_order, context)
            self.pool.get('intervention.request').write(cr, uid, ids, {'state': 'confirmed'}, context)
            return self.open_work_order(cr, uid, order_id, context)    

    def send_email(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'intervention.request',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if any(x.state == 'confirmed' for x in self.browse(cr, uid, ids, context=context)):
            raise osv.except_osv(_('Error!'),  _('You cannot delete a confirmed intervention request.'))
        return super(intervention_request, self).unlink(cr, uid, ids, context=context)

intervention_request()
