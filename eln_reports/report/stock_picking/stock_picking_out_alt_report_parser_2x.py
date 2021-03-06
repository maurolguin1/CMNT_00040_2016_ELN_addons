# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011-2017 QUIVAL, S.A. All Rights Reserved
#    $Pedro Gómez Campos$ <pegomez@elnogal.com>
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
from openerp import pooler, _
from openerp.addons import jasper_reports
from datetime import datetime

def parser( cr, uid, ids, data, context ):
    parameters = {}
    ids = ids
    name = 'report.stock_picking_out_alt_2x'
    model = 'stock.picking'
    data_source = 'model'
    picking = pooler.get_pool(cr.dbname).get('stock.picking').browse(cr,uid,ids)
    language = picking and picking[0].partner_id.lang or False
    context['lang'] = language

    return {
        'ids': ids,
        'name': name,
        'model': model,
        'records': [],
        'data_source': data_source,
        'parameters': parameters,
    }
jasper_reports.report_jasper( 'report.stock_picking_out_alt_2x', 'stock.picking', parser )
