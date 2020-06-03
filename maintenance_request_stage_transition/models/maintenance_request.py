# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv.orm import setup_modifiers
from lxml import etree


class MaintenanceRequest(models.Model):

    _inherit = 'maintenance.request'

    stage_id = fields.Many2one(
        'maintenance.stage',
        readonly=True
    )

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == "form":
            doc = etree.XML(res["arch"])
            stages = self.env['maintenance.stage'].search(
                [], order="sequence desc")
            header = doc.xpath("//form/header")[0]
            for stage in stages:
                node = stage._get_stage_node()
                setup_modifiers(node)
                header.insert(0, node)
            res["arch"] = etree.tostring(doc, encoding="unicode")
        return res

    def create_repair_order(self):
        rec = []
        if self.maintenance_required == 'y':
            if self.have_repair == False:
                rec.append((0, 0, {'product_id': self.equipment_id.product_id.id,'name':self.equipment_id.product_id.name,
                                   'price_unit':self.equipment_id.product_id.standard_price,'product_uom':self.equipment_id.product_id.uom_id.id}))
                repair_order = self.env['repair.order'].create({'product_id':self.equipment_id.product_id.id,
                                                                'product_qty':1,
                                                                'maintenance_code':self.code,
                                                                'product_uom':self.equipment_id.product_id.uom_id.id,
                                                                'have_maintenance':True,
                                                                'fees_lines':rec})
                self.have_repair = True


    def set_maintenance_stage(self):
        self.create_repair_order()
        if not self.env.context.get('next_stage_id'):
            return {}
        return self._set_maintenance_stage(
            self.env.context.get('next_stage_id'))

    def _set_maintenance_stage(self, stage_id):
        self.write({
            'stage_id': stage_id
        })
