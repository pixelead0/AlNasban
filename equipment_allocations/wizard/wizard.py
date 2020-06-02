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


class ReasonWizard(models.TransientModel):
    _name = "reason.wizard"
    _description = "Wizard for getting reason from use on cancel an allocation request."

    reason = fields.Text(string="Reason", required=True)

    @api.multi
    def get_reason(self):
        record = self.env['allocation.request'].browse(
            self._context.get('active_id'))
        ctx = self._context.copy()
        ctx.update({'cancel': True,'reason':self.reason})
        record.with_context(ctx).write({'state': 'cancel'})
        if record.type == "permanent":
            record.equipment_id.sudo().equipment_assign_to = "other"
            record.equipment_id.sudo().owner_user_id = False
