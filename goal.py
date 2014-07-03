#The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Distribution', 'Goal']
__metaclass__ = PoolMeta


class NaturalYearMixin:

    @classmethod
    def __setup__(cls):
        super(NaturalYearMixin, cls).__setup__()

        @staticmethod
        def default_month_field():
            return Decimal('0.0')

        for month in range(1, 13):
            month_str = '%2.2d' % month
            if not hasattr(cls, 'month_%s' % month_str):
                label = 'Month %s' % month_str
                digits = (16, Eval('currency_digits', 2)) if hasattr(cls,
                    'currency_digits') else (16, 2)
                depends = ['currency_digits'] if hasattr(cls,
                    'currency_digits') else []
                field = fields.Function(fields.Numeric(label,
                        digits=digits, depends=depends),
                    'get_month_field', setter='set_month_field')
                setattr(cls, 'month_%s' % month_str, field)
                setattr(cls, 'default_month_%s' % month_str,
                    default_month_field)

    @classmethod
    def get_month_field(cls, instances, names):
        pool = Pool()
        Target = pool.get(cls.lines.model_name)
        res = {}
        ids = [x.id for x in instances]
        for name in names:
            res[name] = {}.fromkeys(ids, Decimal('0.0'))

        parent_name = cls.lines.field
        for line in Target.search([
                    (parent_name, 'in', ids),
                    ]):
            if line.name in res:
                parent_id = getattr(line, parent_name).id
                res[line.name][parent_id] = line.value
        return res

    @classmethod
    def set_month_field(cls, instances, name, value):
        pool = Pool()
        Target = pool.get(cls.lines.model_name)
        to_write = []
        to_create = []
        line_name = name
        for instance in instances:
            for line in instance.lines:
                if line.name == line_name:
                    to_write.append(line)
                    break
            else:
                to_create.append({
                        cls.lines.field: instance.id,
                        'value': value,
                        'name': line_name,
                        })
        if to_write:
            Target.write(to_write, {'value': value})
        if to_create:
            Target.create(to_create)


class Distribution(NaturalYearMixin):
    __name__ = 'sale.goal.distribution'


class Goal(NaturalYearMixin):
    __name__ = 'sale.goal'

    @classmethod
    def __setup__(cls):
        super(Goal, cls).__setup__()

        def on_change_month_field(field_name):
            @fields.depends('distribution')
            def method(self):
                res = {}
                if self.distribution:
                    res['distribution'] = None
                return res
            return method

        for month in range(1, 13):
            field_name = 'month_%2.2d' % month
            if not hasattr(cls, 'on_change_%s' % field_name):
                setattr(cls, 'on_change_%s' % field_name,
                    on_change_month_field(field_name))
                getattr(cls, field_name).on_change.add('distribution')

    def update_lines(self):
        res = super(Goal, self).update_lines()
        if 'lines' in res:
            for _, line in res['lines'].get('add', []):
                res[line['name']] = line['value']
        return res
