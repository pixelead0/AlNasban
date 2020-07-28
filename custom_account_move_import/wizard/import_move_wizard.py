import os
import io
import tempfile
import base64
import logging

from xlrd import open_workbook

from odoo import api, fields, models, _
from odoo.tools import pycompat
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

class CustomAccountMoveFiles(models.TransientModel):
    _name = 'custom.account.move.import.files'
    _description = 'Custom Files Import '

    import_wiz_id = fields.Many2one('custom.account.move.import', string="Import wizard")
    csv_file = fields.Binary(string='File', required=1)
    filename = fields.Char(string='Filename')

class CustomAccountMove(models.TransientModel):
    _name = 'custom.account.move.import'
    _description = 'Import Journal Entries'

    csv_file = fields.Binary(string='File')
    filename = fields.Char(string='Filename')
    sale_journal_id = fields.Many2one('account.journal', string="Sales Journal",
                                     domain="[('type', '=', 'sale')]")
    sale_account_id = fields.Many2one('account.account', string='Product Sales Account', required=1,
                                      domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]")
    receivable_account_id = fields.Many2one('account.account', string='Receivable Account', required=1,
                                            domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]")
    tax_id = fields.Many2one('account.tax', string="Sales Tax", required=1,
                             domain="[('type_tax_use', '=', 'sale')]")
    inventory_account_id = fields.Many2one('account.account', string='Inventory Account',
                                            domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]",
                                            help="This account will be used to reduce the inventory after Sales Process")
    cogs_account_id = fields.Many2one('account.account', string='COGS Account',
                                            domain="[('internal_type', '=', 'other'), ('deprecated', '=', False)]",
                                            help="This account will be used to calculate the Cost of Goods sold after Sales Process")
    is_historic_import = fields.Boolean("Is historic Data ?")
    entry_date = fields.Date("Historic Entry Date")
    import_file_ids = fields.One2many('custom.account.move.import.files', 'import_wiz_id', string='Select Files')

    @api.model
    def default_get(self, fields):
        result = super(CustomAccountMove, self).default_get(fields)
        company = self.env.user.company_id
        result.update({
                        'sale_account_id': company.sale_account_id.id,
                        'receivable_account_id': company.receivable_account_id.id,
                        'tax_id': company.tax_id.id,
                        'inventory_account_id': company.inventory_account_id.id,
                        'cogs_account_id': company.cogs_account_id.id,
                      })
        return result

    @api.multi
    def import_account_move(self):
        datafile = self.csv_file
        file_name = str(self.filename)
        if not datafile or not file_name.lower().endswith(('.csv')):
            raise Warning(_("Please Select .csv file to Import"))
        account_journal_obj = self.env['account.journal']
        analytic_account_obj = self.env['account.analytic.account']
        acc_move_obj = self.env['account.move']
        csv_data = base64.decodestring(datafile)
        f = io.BytesIO(csv_data)
        reader = pycompat.csv_reader(f, quotechar='"', delimiter=',')
        # First line of file (contains columns labels)
        fields = next(reader)
        move_lines = []
        move_ids = []
        main_move = False
        sale_account_id = self.sale_account_id.id
        tax_id = self.tax_id.id
        tax_credit = 0.0
        debit = 0.0
        cogs = 0.0
        cash_move_dict = {}
        for line in reader:
            analytic_acc_id = analytic_account_obj.search([('micros_store_id', '=', int(line[0]))], limit=1)
            if not analytic_acc_id:
                raise Warning("No Analytic account found with Store Id: %s" % line[0])
            if not main_move:
                main_move = acc_move_obj.create({'journal_id': self.sale_journal_id.id,
                                                'date': line[3],
                                                'ref': "Sales Entries Imported from " + file_name,
                                                'micros_file_name': file_name,
                                                })
                move_ids.append(main_move.id)
            if line[6] != '0':
                sales_move_line_vals = {
                    'name': line[2],
                    'micros_tax_number': line[4],
                    'analytic_account_id': analytic_acc_id.id,
                    'account_id': sale_account_id,
                    'credit': float(line[7]),
                    'tax_ids': [(6, 0, [tax_id])],
                                          }
                move_lines.append((0, 0, sales_move_line_vals))
                tax_credit += round(float(line[6]), 2)
                debit += float(line[8])
                if len(line) > 9:
                    cogs += float(line[9])
            else:
                if line[2] in cash_move_dict:
                    tmp = cash_move_dict.get(line[2])

                    cash_move_dict.update({line[2]: tmp + float(line[8])})
                else:
                    cash_move_dict.update({line[2]: float(line[8])})
        if tax_credit:
            tax_move_line_vals = {
                'name': self.tax_id.name,
                'account_id': sale_account_id,
                'credit': tax_credit,
                'tax_line_id': tax_id,
            }
            move_lines.append((0, 0, tax_move_line_vals))
        if debit:
            debit_move_line_vals = {
                'name': "Trade Receivables",
                'account_id': self.receivable_account_id.id,
                'debit': debit,
            }

            move_lines.append((0, 0, debit_move_line_vals))
        if move_lines:
            main_move.write({"line_ids": move_lines})
        move_ref = main_move.name
        for journal,debit_amount in cash_move_dict.items():
            move_lines = []
            journal_id = account_journal_obj.search([('type', 'in', ['bank', 'cash']),('name', '=', journal.replace("'",""))], limit=1)
            if not journal_id:
                raise Warning("No Journal found with Name: %s" % journal)
            main_move = acc_move_obj.create({'journal_id': journal_id.id,
                                             'date': line[3],
                                             'ref': "Payment Entries Imported from " + file_name,
                                             })
            move_ids.append(main_move.id)
            debit_move_line_vals = {
                'name': move_ref,
                'account_id': journal_id.default_credit_account_id.id,
                'debit': debit_amount,
            }
            move_lines.append((0, 0, debit_move_line_vals))
            credit_move_line_vals = {
                'name': "Customer Payment: " + move_ref,
                'account_id': self.receivable_account_id.id,
                'credit': debit_amount,
            }
            move_lines.append((0, 0, credit_move_line_vals))
            main_move.write({"line_ids": move_lines})
        if cogs:
            cogs_main_move = acc_move_obj.create({'journal_id': self.sale_journal_id.id,
                                             'date': line[3],
                                             'ref': "COGS Entries Imported from " + file_name,
                                             })
            move_ids.append(cogs_main_move.id)
            cogs_main_move.write({"line_ids": [(0, 0, {
                                                        'name': "Inventory Entry: " + move_ref,
                                                        'account_id': self.inventory_account_id.id,
                                                        'credit': cogs}),
                                               (0, 0, {
                                                        'name': "COGS Entry: " + move_ref,
                                                        'account_id': self.cogs_account_id.id,
                                                        'debit': cogs})]
                                })
        if move_ids:
            return self.action_view_account_move(move_ids)

    @api.multi
    def import_historic_account_move(self):

        analytic_account_obj = self.env['account.analytic.account']
        sale_account_id = self.sale_account_id.id
        acc_move_obj = self.env['account.move']
        move_ids = []
        for each_import_file in self.import_file_ids:
            datafile = each_import_file.csv_file
            file_name = str(each_import_file.filename)
            if not datafile or not \
                    file_name.lower().endswith(('.xlsx')):
                raise Warning(_("Please Select .xlsx file to Import"))
            file_data = base64.decodestring(datafile)
            move_lines = []
            temp_path = tempfile.gettempdir()
            fp = open(temp_path + '/xsl_file.xls', 'wb+')
            tax_id = self.tax_id
            fp.write(file_data)
            fp.close()
            wb = open_workbook(temp_path + '/xsl_file.xls')
            for sheet in wb.sheets():
                dates = sheet.row_values(1) and sheet.row_values(1)[1] or ''
                analytic_account_name = sheet.row_values(2) and sheet.row_values(2)[1] or ''
                if analytic_account_name:
                    sale_journal_id = self.env.user.company_id.sale_journal_id
                    if not sale_journal_id:
                        raise Warning("No Sales Journal configured in Company Config.")
                    sale_entry_line = sheet.row_values(5)

                    # Get the Analytic Account
                    analytic_account_rec = analytic_account_obj.search(
                        [('name', '=', analytic_account_name)]
                    )
                    if not analytic_account_rec:
                        raise Warning("No Analytic Account found with Name: %s" % analytic_account_name)

                    # Sales Move with two lines
                    main_move = acc_move_obj.create({'journal_id': sale_journal_id.id,
                                                     'date': self.entry_date,
                                                     'ref': "Historic Sales Entries Imported from " + file_name + ", Date: "+ \
                                                            dates,
                                                     'micros_file_name': analytic_account_name + '-' + dates,
                                                         })
                    move_ids.append(main_move.id)
                    full_sheet_total = sale_entry_line[1]
                    tax_amount = 0

                    for rownum in range(6, sheet.nrows):
                        payment_line = sheet.row_values(rownum)
                        if payment_line[1]:
                            payment_ref = payment_line[0]

                            # Get the Analytic TAG
                            analytic_tag_rec = self.env['account.analytic.tag'].search(
                                ['|', ('name', '=', payment_ref),
                                 ('alternate_names_ids.name', '=', payment_ref)]
                            )
                            if not analytic_tag_rec:
                                raise Warning("No Analytic Account TAG with Name: %s" % payment_ref)
                            if not analytic_tag_rec.account_id:
                                raise Warning("No Account defined in Tag: %s" % analytic_tag_rec.name)

                            if not analytic_tag_rec.separate_jv_line:
                                debit_move_line_vals = {
                                    'analytic_account_id': analytic_account_rec.id,
                                    'account_id': analytic_tag_rec.account_id.id,
                                    'debit': float(payment_line[1]),
                                    'analytic_tag_ids': [(6, 0, [analytic_tag_rec.id])],
                                    'partner_id': analytic_tag_rec.partner_id.id,
                                }
                                move_lines.append((0, 0, debit_move_line_vals))
                            else:
                                credit_move_line_vals = {
                                    'analytic_account_id': analytic_account_rec.id,
                                    'account_id': analytic_tag_rec.account_id.id,
                                    'debit': float(payment_line[1]),
                                    'analytic_tag_ids': [(6, 0, [analytic_tag_rec.id])],
                                    'partner_id': analytic_tag_rec.partner_id.id,
                                }
                                move_lines.append((0, 0, credit_move_line_vals))

                                credit_amount = float(payment_line[1]) / (1 + (tax_id.amount / 100))
                                credit_amount = round(credit_amount, 2)
                                debit_move_line_vals = {
                                    'name': 'Credit',
                                    'analytic_account_id': analytic_account_rec.id,
                                    'account_id': sale_account_id,
                                    'credit': credit_amount,
                                    'partner_id': analytic_tag_rec.partner_id.id,
                                    'tax_ids': [(6, 0, [tax_id.id])],
                                }
                                move_lines.append((0, 0, debit_move_line_vals))
                                tax_amount += round(float(payment_line[1]) - credit_amount, 2)
                                full_sheet_total -= float(payment_line[1])

                    credit = float(full_sheet_total) / (1 + (tax_id.amount / 100))
                    credit = round(credit, 2)
                    tax_amount += round(float(full_sheet_total) - credit, 2)

                    # Add Credit Line
                    sales_move_line_vals = {
                        'name': sale_entry_line[0],
                        'analytic_account_id': analytic_account_rec.id,
                        'account_id': sale_account_id,
                        'credit': credit,
                        'tax_ids': [(6, 0, [tax_id.id])],
                    }
                    move_lines.append((0, 0, sales_move_line_vals))

                    # Create Tax line
                    tax_move_line_vals = {
                        'name': tax_id.name,
                        'account_id': tax_id.account_id.id,
                        'credit': tax_amount,
                        'analytic_account_id': analytic_account_rec.id,
                        'tax_line_id': tax_id.id,
                    }
                    move_lines.append((0, 0, tax_move_line_vals))
                    move_lines.reverse()
                    main_move.write({"line_ids": move_lines})
            try:
                os.unlink(temp_path + '/xsl_file.xls')
            except (OSError, IOError):
                _logger.error('Error when trying to remove file %s' % temp_path + '/xsl_file.xls')
        if move_ids:
            return self.action_view_account_move(move_ids)


    @api.multi
    def action_view_account_move(self, move_ids):
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result['context'] = {}
        result['domain'] = "[('id','in',%s)]" % (move_ids)
        return result
