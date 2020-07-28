# -*- coding: utf-8 -*-

from .base_tech import *


# class ReportGeneralLedger(models.AbstractModel):
#     _inherit = 'report.account.report_generalledger'

    #
    # def _get_account_move_entry(self, accounts, init_balance, sortby, display_account, analytic_ids, project_ids):
    #     """
    #     :param:
    #             accounts: the recordset of accounts
    #             init_balance: boolean value of initial_balance
    #             sortby: sorting by date or partner and journal
    #             display_account: type of account(receivable, payable and both)
    #
    #     Returns a dictionary of accounts with following key and value {
    #             'code': account code,
    #             'name': account name,
    #             'debit': sum of total debit amount,
    #             'credit': sum of total credit amount,
    #             'balance': total balance,
    #             'amount_currency': sum of amount_currency,
    #             'move_lines': list of move line
    #     }
    #     """
    #     cr = self.env.cr
    #     MoveLine = self.env['account.move.line']
    #     move_lines = dict(map(lambda x: (x, []), accounts.ids))
    #
    #     where_analytic = ''
    #     if analytic_ids:
    #         where_analytic = ' and analytic_account_id in (%s) ' % (','.join([str(x) for x in analytic_ids]))
    #     where_project = ''
    #     if project_ids:
    #         where_project = ' and project_id in (%s) ' % (','.join([str(x) for x in project_ids]))
    #     # Prepare initial sql query and Get the initial move lines
    #     if init_balance:
    #         init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False,
    #                                                                                   initial_bal=True)._query_get()
    #         init_wheres = [""]
    #         if init_where_clause.strip():
    #             init_wheres.append(init_where_clause.strip())
    #         init_filters = " AND ".join(init_wheres)
    #         filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
    #         sql = ("SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
    #             '' AS move_name, '' AS mmove_id, '' AS currency_code,\
    #             NULL AS currency_id,\
    #             '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
    #             '' AS partner_name\
    #             FROM account_move_line l\
    #             LEFT JOIN account_move m ON (l.move_id=m.id)\
    #             LEFT JOIN res_currency c ON (l.currency_id=c.id)\
    #             LEFT JOIN res_partner p ON (l.partner_id=p.id)\
    #             LEFT JOIN account_invoice i ON (m.id =i.move_id)\
    #             JOIN account_journal j ON (l.journal_id=j.id)\
    #             WHERE l.account_id IN %s" + filters + where_analytic + where_project + ' GROUP BY l.account_id')
    #         params = (tuple(accounts.ids),) + tuple(init_where_params)
    #         cr.execute(sql, params)
    #         for row in cr.dictfetchall():
    #             move_lines[row.pop('account_id')].append(row)
    #
    #     sql_sort = 'l.date, l.move_id'
    #     if sortby == 'sort_journal_partner':
    #         sql_sort = 'j.code, p.name, l.move_id'
    #
    #     # Prepare sql query base on selected parameters from wizard
    #     tables, where_clause, where_params = MoveLine._query_get()
    #     wheres = [""]
    #     if where_clause.strip():
    #         wheres.append(where_clause.strip())
    #     filters = " AND ".join(wheres)
    #     filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
    #
    #     # Get move lines base on sql query and Calculate the total balance of move lines
    #     sql = ('SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, '
    #            'l.name AS lname, COALESCE(l.debit,0) AS debit, '
    #            'COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,'
    #            'project_id as lproject, analytic_account_id as lanalytic, \
    #             m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
    #             FROM account_move_line l\
    #             JOIN account_move m ON (l.move_id=m.id)\
    #             LEFT JOIN res_currency c ON (l.currency_id=c.id)\
    #             LEFT JOIN res_partner p ON (l.partner_id=p.id)\
    #             JOIN account_journal j ON (l.journal_id=j.id)\
    #             JOIN account_account acc ON (l.account_id = acc.id) \
    #             WHERE l.account_id IN %s ' + filters + where_analytic + where_project + ' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ' + sql_sort)
    #     params = (tuple(accounts.ids),) + tuple(where_params)
    #     cr.execute(sql, params)
    #
    #     for row in cr.dictfetchall():
    #         balance = 0
    #         for line in move_lines.get(row['account_id']):
    #             balance += line['debit'] - line['credit']
    #         row['balance'] += balance
    #         move_lines[row.pop('account_id')].append(row)
    #
    #     # Calculate the debit, credit and balance for Accounts
    #     account_res = []
    #     for account in accounts:
    #         currency = account.currency_id and account.currency_id or account.company_id.currency_id
    #         res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
    #         res['code'] = "[%s]" % account.final_code
    #         res['name'] = account.name
    #         res['move_lines'] = move_lines[account.id]
    #         for line in res.get('move_lines'):
    #             res['debit'] += line['debit']
    #             res['credit'] += line['credit']
    #             res['balance'] = line['balance']
    #         if display_account == 'all':
    #             account_res.append(res)
    #         if display_account == 'movement' and res.get('move_lines'):
    #             account_res.append(res)
    #         if display_account == 'not_zero' and not currency.is_zero(res['balance']):
    #             account_res.append(res)
    #
    #     return account_res



class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    target_move = fields.Selection(default='all')

    def default_get(self, fields_list):
        res = super(AccountCommonReport, self).default_get(fields_list)
        res['target_move'] = 'all'
        return {}
