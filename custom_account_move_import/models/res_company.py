# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCompany(models.Model):

    _inherit = 'res.company'

    # For AML Import
    sale_account_id = fields.Many2one('account.account', string='Product Sales Account',
                                      domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]")
    receivable_account_id = fields.Many2one('account.account', string='Receivable Account',
                                            domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]")
    tax_id = fields.Many2one('account.tax', string="Sales Tax",
                             domain="[('type_tax_use', '=', 'sale')]")
    sale_journal_id = fields.Many2one('account.journal', string="Sales Journal",
                             domain="[('type', '=', 'sale')]")
    inventory_account_id = fields.Many2one('account.account', string='Inventory Account',
                                            domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]",
                                            help="This account will be used to reduce the inventory after Sales Process")
    cogs_account_id = fields.Many2one('account.account', string='COGS Account',
                                            domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]",
                                            help="This account will be used to calculate the Cost of Goods sold after Sales Process")
    # For Vendor Bill Import
    product_id = fields.Many2one('product.product', string="Product")
    purchase_journal_id = fields.Many2one('account.journal', string="Purchase Journal",
                                          domain="[('type', '=', 'purchase')]")
    expense_account_id = fields.Many2one('account.account', string='Bill Line Account',
                                         domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]")
    payable_account_id = fields.Many2one('account.account', string='Payable Account',
                                         domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]")
    purchase_tax_id = fields.Many2one('account.tax', string="Purchase Tax",
                            domain="[('type_tax_use', '=', 'purchase')]")
    # To Map Actual Payment methods during Historical Import
    actual_payment_methods = fields.Char("Payment methods names",
                                         help="Comma-separated values with all names of Payment methods w/o any suffix")
