# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
##############################################################################
from openerp import models, fields, api, exceptions, _

class StcokPickingAssignMulti(models.TransientModel):

    _name = 'stock.picking.assign.multi'

    @api.multi
    def assign(self):
        self.ensure_one()
        picking_ids = self._context.get('active_ids', False)
        pickings = self.env['stock.picking'].browse(picking_ids)
        pickings = pickings.filtered(
            lambda r: r.state in ['partially_available', 'confirmed'])
        pickings.action_assign()
        return {'type': 'ir.actions.act_window_close'}
