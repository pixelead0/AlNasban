# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import logging

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class RequestAllocatedWizard(models.TransientModel):
    _name = "request.allocated.wizard"
    _description = "Wizard for allocated equipment to other user"

    message = fields.Text(string="Message")

    @api.multi
    def approve_equipment(self):
        record = self.env['allocation.request'].browse(
            self._context.get('active_id'))
        ctx = self._context.copy()
        ctx.update({'approved': True})
        if record.state == "new":
            request_id = self.env['allocation.request'].search(
                [('equipment_id', '=', record.equipment_id.id),
                 ('state', 'in', ['approved'])], limit=1)
            if request_id:
                vals = {
                    'reason': "Approved for another request so cancelled it."}
                wizard = self.env['reason.wizard'].create(vals)
                context = ctx.copy()
                context.update({'active_id': request_id.id})
                wizard.with_context(context).get_reason()
            else:
                request_id = self.env['allocation.request'].search(
                    [('equipment_id', '=', record.equipment_id.id),
                     ('state', 'in', ['allocated'])], limit=1)
                if request_id:
                    request_id.set_returned()
        record.with_context(ctx).write({'state': 'approved'})
