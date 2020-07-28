from odoo import models, fields, api
from num2words import num2words

class InheritAccount(models.Model):
    _inherit = 'account.invoice'
    assign_custody = fields.Many2one('hr.employee', string='Assign Custody')
    tax_id = fields.Char(related='partner_id.vat', string='Tax ID')
    text_amount = fields.Char(required=False, compute="amount_to_words")
    
    @api.one
    @api.depends('amount_total')
    def amount_to_words(self):
        if self.company_id.text_amount_language_currency:
            self.text_amount = num2words(self.amount_total, to='currency',
                                         lang=self.company_id.text_amount_language_currency)

    def get_driver(self):
        driver = ''
        vehicle = ''
        sale_obj = self.env['sale.order'].search([('name', '=', self.origin)])
        driver = sale_obj.driver_name.name
        vehicle = sale_obj.vehicle
        return driver, vehicle

class InheritSale(models.Model):
    _inherit = 'sale.order'
    driver_name = fields.Many2one('hr.employee', string='Driver name')
    vehicle = fields.Char('Vehicle No.')


class InheritPartner(models.Model):
    _inherit = 'res.company'
    fax = fields.Char(string='Fax')
    po_box = fields.Char(string='P.O Box')
    company_tag = fields.Char()
    text_amount_language_currency = fields.Selection([('en', 'English'),
                                                      ('ar', 'Arabic'),
                                                      ('cz ', 'Czech'),
                                                      ('de', 'German'),
                                                      ('dk', 'Danish'),
                                                      ('en_GB', 'English - Great Britain'),
                                                      ('en_IN', 'English - India'),
                                                      ('es', 'Spanish'),
                                                      ('es_CO', 'Spanish - Colombia'),
                                                      ('es_VE', 'Spanish - Venezuela'),
                                                      ('eu', 'EURO'),
                                                      ('fi', 'Finnish'),
                                                      ('fr', 'French'),
                                                      ('fr_CH', 'French - Switzerland'),
                                                      ('fr_BE', 'French - Belgium'),
                                                      ('fr_DZ', 'French - Algeria'),
                                                      ('he', 'Hebrew'),
                                                      ('id', 'Indonesian'),
                                                      ('it', 'Italian'),
                                                      ('ja', 'Japanese'),
                                                      ('ko', 'Korean'),
                                                      ('lt', 'Lithuanian'),
                                                      ('lv', 'Latvian'),
                                                      ('no', 'Norwegian'),
                                                      ('pl', 'Polish'),
                                                      ('pt', 'Portuguese'),
                                                      ('pt_BR', 'Portuguese - Brazilian'),
                                                      ('sl', 'Slovene'),
                                                      ('sr', 'Serbian'),
                                                      ('ro', 'Romanian'),
                                                      ('ru', 'Russian'),
                                                      ('sl', 'Slovene'),
                                                      ('tr', 'Turkish'),
                                                      ('th', 'Thai'),
                                                      ('vi', 'Vietnamese'),
                                                      ('nl', 'Dutch'),
                                                      ('uk', 'Ukrainian'),
                                                      ], string='Text amount language/currency')

class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    text_amount_language_currency = fields.Selection(related="company_id.text_amount_language_currency",
                                                         string='language_currency', readonly=False)

    @api.onchange('text_amount_language_currency')
    def save_text_amount_language_currency(self):
        if self.text_amount_language_currency:
            self.company_id.text_amount_language_currency = self.text_amount_language_currency
