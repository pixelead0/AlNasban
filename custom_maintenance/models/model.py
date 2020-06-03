from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import ValidationError

class InheritMaintenance(models.Model):
    _inherit = 'maintenance.request'
    department = fields.Many2one('hr.department')
    maintenance_required = fields.Selection([('y','Yes'),('n','No')],default='n')
    repair_count = fields.Integer(compute='_repair_count')
    have_repair = fields.Boolean(default=False)

    def repair_view(self):
        rep_ids = []
        for obj in self:
            rep_obj = self.env['repair.order'].sudo().search([])
            repair_id = rep_obj.filtered(
                lambda x: x.maintenance_code == self.code)
            for item in repair_id:
                rep_ids.append(item.id)
            view_id = self.env.ref('repair.view_repair_order_form').id
            if rep_ids:
                value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'repair.order',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Repair Order'),
                        'res_id': rep_ids and rep_ids[0]
                    }
                return value

    @api.multi
    def _repair_count(self):
        for obj in self:
            repair_ids = self.env['repair.order'].sudo().search([])
            repairs = repair_ids.filtered(lambda x: x.maintenance_code == self.code)
        obj.repair_count = len(repairs)



class InheritRepair(models.Model):
    _inherit = 'repair.order'
    maintenance_count = fields.Integer(compute='_maintenance_count')
    maintenance_code = fields.Char()
    have_maintenance = fields.Boolean(default=False)


    def maintenance_view(self):
        maintenance_ids = []
        for obj in self:
            maintenance_obj = self.env['maintenance.request'].sudo().search([])
            maintenance_id = maintenance_obj.filtered(
                lambda x: x.code == self.maintenance_code)
            for item in maintenance_id:
                maintenance_ids.append(item.id)
            view_id = self.env.ref('maintenance.hr_equipment_request_view_form').id
            if maintenance_ids:
                value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'maintenance.request',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Maintenance Request'),
                        'res_id': maintenance_ids and maintenance_ids[0]
                    }
                return value


    @api.multi
    def _maintenance_count(self):
        for obj in self:
            maintenance_ids = self.env['maintenance.request'].sudo().search([])
            maintenance = maintenance_ids.filtered(lambda x: x.code == self.maintenance_code)
        obj.maintenance_count = len(maintenance)
