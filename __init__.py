# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .goal import *


def register():
    Pool.register(
        Distribution,
        Goal,
        module='sale_goal_natural_year', type_='model')
