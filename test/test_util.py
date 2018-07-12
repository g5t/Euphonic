import unittest
import math
import numpy.testing as npt
from pint import UnitRegistry
from casteppy.util import set_up_unit_registry, reciprocal_lattice


class TestSetUpUnitRegistry(unittest.TestCase):

    def test_returns_unit_registry(self):
        self.assertIsInstance(set_up_unit_registry(),
                              type(UnitRegistry()))

    def test_has_rydberg_units(self):
        ureg = set_up_unit_registry()
        test_ev = 1 * ureg.Ry
        test_ev.ito(ureg.eV)
        self.assertEqual(test_ev.magnitude, 13.605693009)


class TestReciprocalLattice(unittest.TestCase):

    def test_identity(self):
        recip = reciprocal_lattice([[1., 0., 0.],
                                    [0., 1., 0.],
                                    [0., 0., 1.]])
        expected_recip = [[2*math.pi, 0., 0.],
                          [0., 2*math.pi, 0.],
                          [0., 0., 2*math.pi]]
        npt.assert_allclose(recip, expected_recip)

    def test_graphite(self):
        recip = reciprocal_lattice([[ 4.025915, -2.324363,  0.000000],
                                    [-0.000000,  4.648726,  0.000000],
                                    [ 0.000000,  0.000000, 12.850138]])
        expected_recip = [[1.56068503860106, 0., 0.],
                          [0.780342519300529, 1.3515929541082, 0.],
                          [0., 0., 0.488958586061845]]

        npt.assert_allclose(recip, expected_recip)

    def test_iron(self):
        recip = reciprocal_lattice([[-2.708355,  2.708355,  2.708355],
                                    [ 2.708355, -2.708355,  2.708355],
                                    [ 2.708355,  2.708355, -2.708355]])
        expected_recip = [[0., 1.15996339, 1.15996339],
                          [1.15996339, 0., 1.15996339],
                          [1.15996339, 1.15996339, 0.]]
        npt.assert_allclose(recip, expected_recip)
