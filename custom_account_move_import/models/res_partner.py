# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):

    _inherit = 'res.partner'

    linked_analytic_account_id = fields.Many2one("account.analytic.account",
                                                 string="Analytic Account")
    micros_alternative_name = fields.Char("Alternative name", copy=False)
