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


class ReplaceEquipmentWizard(models.TransientModel):
    _name = "replace.equipment.wizard"
    _description = "Wizard for replace equipment of the user"

    @api.model
    def get_default_department(self):
        obj = self.env['allocation.request'].browse(
            self._context.get('active_id'))
        if obj.request_user_id.sudo().employee_ids and obj.request_user_id.sudo().employee_ids[0].department_id:
            return obj.request_user_id.sudo().employee_ids[0].department_id.id
        return False

    @api.model
    def get_category_id(self):
        obj = self.env['allocation.request'].browse(
            self._context.get('active_id'))
        return obj.category_id.id

    @api.model
    def get_equipment_domain(self):
        department_id = self.get_default_department()
        if not self.env.user._is_admin():
            if not department_id:
                raise UserError(
                    _("Employee Department not set. Please contact Hr Department."))
        equipment_ids = []
        category_id = self.category_id.id or self.get_category_id()
        if category_id:
            equipment_ids += self.env['maintenance.equipment'].search(
                [('category_id', '=', category_id),
                 ('owner_user_id', '=', False), ('department_id', '=', False)]).ids
        return equipment_ids

    category_id = fields.Many2one('maintenance.equipment.category',
                                  string='Category', required=True,
                                  default=get_category_id
                                  )
    equipment_id = fields.Many2one(
        'maintenance.equipment', string='Equipment', domain=lambda self: [('id', 'in', self.get_equipment_domain())])
    
    reason = fields.Text(string="Message")

    @api.multi
    def replace_equipment(self):
        context = self._context.copy()
        context.update({'replace_equipment': True, 'reason': self.reason})
        request_obj = self.env['allocation.request'].browse(
            self._context.get('active_id'))
        old_equipment = request_obj.equipment_id
        request_obj.release_equipment()
        old_equipment.sudo().equipment_assign_to = "other"
        old_equipment.sudo().owner_user_id = False
        request_obj.with_context(context).equipment_id = self.equipment_id.id
        request_obj.allocate_resource()
        request_obj.sudo().equipment_id.equipment_assign_to = 'employee'
        request_obj.sudo().equipment_id.owner_user_id = request_obj.request_user_id
        subject_html = "Equipment " + old_equipment.display_name + \
            ' has been replaced by ' + self.equipment_id.display_name
        template = self.env['ir.model.data'].xmlid_to_object(
            'equipment_allocations.email_equipment_replace')
        Template = self.env['mail.template']
        context.update({'old_equipment':old_equipment.display_name})
        if template:
            template = template.with_context(
                context).get_email_template(request_obj.id)
            body_html = Template.with_context(template._context)._render_template(
                template.body_html, 'allocation.request', request_obj.id)

            request_obj.message_post(
                body=body_html,
                subject=subject_html,
                subtype='mail.mt_comment',
                partner_ids=request_obj.request_user_id.partner_id.ids,
                message_type='comment'
            )
