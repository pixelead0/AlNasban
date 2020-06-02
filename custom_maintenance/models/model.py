from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import ValidationError

class InheritMaintenance(models.Model):
    _inherit = 'maintenance.request'
    department = fields.Many2one('hr.department')
    maintenance_required = fields.Selection([('y','Yes'),('n','No')],default='n')

