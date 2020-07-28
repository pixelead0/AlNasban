# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning

class AccountAnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'

    @api.constrains('micros_store_id')
    def _micros_store_id_uniq(self):
        for rec in self:
            if rec.micros_store_id:
                if self.search_count([('micros_store_id', '=', rec.micros_store_id)]) > 1:
                    raise Warning(_("Micros Store ID already exists !"))

    micros_store_id = fields.Integer(string="Micros Store ID", copy=False)
    micros_store_name = fields.Char(string="Micros Store Name", copy=False)
    micros_alternative_name = fields.Char("Alternative name", copy=False)

    _sql_constraints = [
        ('micros_store_id_uniq', 'unique (id,micros_store_id)', "Micros Store ID already exists !"),
        ('micros_store_name_uniq', 'unique (micros_store_name)', "Micros Store Name already exists !"),

    ]

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    micros_tax_number = fields.Char(string="Micros Transaction ID", readonly=True)

class AccountMove(models.Model):

    _inherit = 'account.move'

    micros_file_name = fields.Char(string="File name",
                                   help="File Used to Import lines",
                                   readonly=True, copy=False)

    _sql_constraints = [
        ('micros_file_name_uniq', 'unique (micros_file_name)', """This file has been already Imported, Please check File name/Locations
 and Business Dates !"""),
    ]

class AccountJournal(models.Model):

    _inherit = 'account.journal'

    linked_analytic_account_id = fields.Many2one("account.analytic.account",
                                                 string="Analytic Account")
    linked_analytic_tag_id = fields.Many2one("account.analytic.tag",
                                             string="Analytic Tag")
