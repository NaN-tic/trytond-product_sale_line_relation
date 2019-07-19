# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields, ModelSQL

__all__ = ['SaleLine']

SALE_LINE_FIELD_MAP = {
    'sale_party': 'party',
    'sale_state': 'state',
    'sale_date': 'sale_date',
    'sale_shipment_party': 'shipment_party',
    }


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'
    sale_party = fields.Function(fields.Many2One('party.party', 'Sale Party'),
        'get_sale_field', searcher='search_sale_field')
    sale_shipment_party = fields.Function(fields.Many2One('party.party',
            'Sale Shipment Party'), 'get_sale_field',
        searcher='search_sale_field')
    sale_date = fields.Function(fields.Date('Sale Date'), 'get_sale_field',
        searcher='search_sale_field')

    shipment_state = fields.Function(fields.Selection([
        ('none','None'), ('waiting', 'Waiting'),('exception', 'Exception'),
        ('sent', 'Sent')],'Shipment State'), 'get_shipment_state',
        searcher='search_shipment_state')

    def get_sale_field(self, name):
        name = SALE_LINE_FIELD_MAP[name]
        if not self.sale:
            return
        value = getattr(self.sale, name)
        if value and isinstance(value, ModelSQL):
            value = value.id
        return value

    @classmethod
    def search_sale_field(cls, name, clause):
        name = SALE_LINE_FIELD_MAP[name]
        return [('sale.' + name,) + tuple(clause[1:])]

    @classmethod
    def get_shipment_state(cls, lines, name):
        result = {}.fromkeys([x.id for x in lines])
        for line in lines:
            result[line.id] = 'waiting'
            if line.move_exception:
                result[line.id] = 'exception'
            elif line.sale == None:
                result[line.id] = 'none'
            elif line.move_done:
                result[line.id] = 'sent'
        return result

    @classmethod
    def search_shipment_state(cls, name, clause):
        n,op, state = clause
        lines = cls.search([('sale.shipment_state', op, state)])
        if state == 'sent':
            partial = cls.search([('sale.shipment_state', op , 'sent')])
            lines += [x for x in partial if x.move_done]

        if state == 'waiting':
            lines = [x for x in lines if not x.move_done]

        if state == None:
            without_sale =cls.search([('sale', '=', None)])
            lines += [x for x in without_sale]
        return [('id', 'in', [x.id for x in lines])]
