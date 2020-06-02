from odoo import api, fields, models


class AllocationHistory(models.Model):
    _name = 'allocation.history'

    equipment_id = fields.Many2one('maintenance.equipment')
    src_location = fields.Many2one('stock.location')
    dest_location = fields.Many2one('stock.location')
    employee_id = fields.Many2one('hr.employee')
    equip_box = fields.Char(related='equipment_id.box_no')
    equip_model = fields.Char(related='equipment_id.model')
    equip_mac = fields.Char(related='equipment_id.mac_add')
    equip_tag = fields.Char(related='equipment_id.tag')
    emp_id = fields.Char(related='employee_id.employee_number')
    status = fields.Selection([('allocated','Allocated'),('return','Returned'),('replaced','Replaced')],default='')
    assingned_by = fields.Many2one('res.users')
    assinged_date = fields.Date()

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.equipment_id.name
            record.name=name
            result.append((record.id, name))
        return result
