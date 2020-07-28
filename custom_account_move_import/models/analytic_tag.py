# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AnalyticTag(models.Model):

    _inherit = 'account.analytic.tag'

    account_id = fields.Many2one('account.account', string='Account',
                                      domain="[('deprecated', '=', False)]", copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner', copy=False)
    separate_jv_line = fields.Boolean('Create Separate JV line?', copy=False)
    alternate_names_ids = fields.One2many(
        'tag.alternate.names', 'analytic_tag_id',
        'Alternate Names', copy=False)


class TagAlternateNames(models.Model):

    _name = 'tag.alternate.names'
    _description = 'Alternate Names'

    name = fields.Char('Alternate Name', required=True)
    analytic_tag_id = fields.Many2one('account.analytic.tag', string='Tag')
