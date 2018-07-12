import unittest
import numpy.testing as npt
from io import StringIO
from pint import UnitRegistry
from casteppy.util import set_up_unit_registry
from casteppy.parsers.general import read_input_file
from casteppy.parsers.phonon import read_dot_phonon, read_dot_phonon_header
from casteppy.parsers.bands import read_dot_bands


class TestReadInputFileNaHBands(unittest.TestCase):

    def setUp(self):
        # Create trivial function object so attributes can be assigned to it
        NaH_bands = lambda:0
        # Need to use actual files here rather than simulating their content
        # with StringIO, in order to test the way the read_input_file function
        # searches for missing data (e.g. ion_pos) in other files
        NaH_bands_file = 'test/data/NaH.bands'
        units = 'hartree'
        up = False
        down = False
        ureg = UnitRegistry()

        with open(NaH_bands_file, 'r') as f:
            (NaH_bands.cell_vec, NaH_bands.ion_pos, NaH_bands.ion_type,
                NaH_bands.kpts, NaH_bands.weights, NaH_bands.freqs,
                NaH_bands.freq_down, NaH_bands.i_intens, NaH_bands.r_intens,
                NaH_bands.eigenvecs, NaH_bands.fermi) = read_input_file(
                    f, ureg, units, up, down)

        NaH_bands.expected_cell_vec = [[0.000000, 4.534397, 4.534397],
                                       [4.534397, 0.000000, 4.534397],
                                       [4.534397, 4.534397, 0.000000]]
        NaH_bands.expected_ion_pos = [[0.500000, 0.500000, 0.500000],
                                      [0.000000, 0.000000, 0.000000]]
        NaH_bands.expected_ion_type = ['H', 'Na']
        NaH_bands.expected_kpts = [[-0.45833333, -0.37500000, -0.45833333],
                                   [-0.45833333, -0.37500000, -0.20833333]]
        NaH_bands.expected_weights = [0.00347222, 0.00694444]
        NaH_bands.expected_freqs = [[-1.83230180, -0.83321119, -0.83021854,
                                     -0.83016941, -0.04792334],
                                    [-1.83229571, -0.83248269, -0.83078961,
                                     -0.83036048, -0.05738470]]
        NaH_bands.expected_freq_down = []
        NaH_bands.expected_fermi = [-0.009615]
        self.NaH_bands = NaH_bands

    def test_cell_vec_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.cell_vec,
                               self.NaH_bands.expected_cell_vec)

    def test_ion_pos_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.ion_pos,
                               self.NaH_bands.expected_ion_pos)

    def test_ion_type_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.ion_type,
                               self.NaH_bands.expected_ion_type)

    def test_kpts_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.kpts,
                               self.NaH_bands.expected_kpts)

    def test_weights_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.weights,
                               self.NaH_bands.expected_weights)

    def test_freqs_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.freqs,
                               self.NaH_bands.expected_freqs)

    def test_freq_down_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.freq_down,
                               self.NaH_bands.expected_freq_down)

    def test_eigenvecs_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.eigenvecs, [])

    def test_fermi_read_nah_bands(self):
        npt.assert_array_equal(self.NaH_bands.fermi,
                               self.NaH_bands.expected_fermi)


class TestReadInputFileNaHPhonon(unittest.TestCase):

    def setUp(self):
        # Create trivial function object so attributes can be assigned to it
        NaH_phonon = lambda:0
        # Need to use actual files here rather than simulating their content
        # with StringIO, in order to test the way the read_input_file function
        # searches for missing data (e.g. ion_pos) in other files
        NaH_phonon_file = 'test/data/NaH.phonon'
        units = '1/cm'
        up = False
        down = False
        ir = False
        raman = False
        read_eigenvecs = True
        ureg = UnitRegistry()

        with open(NaH_phonon_file, 'r') as f:
            (NaH_phonon.cell_vec, NaH_phonon.ion_pos, NaH_phonon.ion_type,
                NaH_phonon.kpts, NaH_phonon.weights, NaH_phonon.freqs,
                NaH_phonon.freq_down, NaH_phonon.i_intens,
                NaH_phonon.r_intens, NaH_phonon.eigenvecs,
                NaH_phonon.fermi) = read_input_file(
                    f, ureg, units, up, down, ir, raman, read_eigenvecs)

        NaH_phonon.expected_cell_vec = [[0.000000, 2.399500, 2.399500],
                                        [2.399500, 0.000000, 2.399500],
                                        [2.399500, 2.399500, 0.000000]]
        NaH_phonon.expected_ion_pos = [[0.500000, 0.500000, 0.500000],
                                       [0.000000, 0.000000, 0.000000]]
        NaH_phonon.expected_ion_type = ['H', 'Na']
        NaH_phonon.expected_kpts = [[-0.250000, -0.250000, -0.250000],
                                    [-0.250000, -0.500000, -0.500000]]
        NaH_phonon.expected_weights = [0.125, 0.375]
        NaH_phonon.expected_freqs = [[91.847109, 91.847109, 166.053018,
                                      564.508299, 564.508299, 884.068976],
                                     [132.031513, 154.825631, 206.213940,
                                      642.513551, 690.303338, 832.120011]]
        NaH_phonon.expected_freq_down = []
        NaH_phonon.expected_eigenvecs = [[[-0.061613336996 - 0.060761142686*1j,
                                           -0.005526816216 - 0.006379010526*1j,
                                            0.067140153211 + 0.067140153211*1j],
                                          [ 0.666530886823 - 0.004641603630*1j,
                                            0.064846864124 + 0.004641603630*1j,
                                           -0.731377750947 + 0.000000000000*1j],
                                          [-0.043088481348 - 0.041294487960*1j,
                                            0.074981829953 + 0.073187836565*1j,
                                           -0.031893348605 - 0.031893348605*1j],
                                          [ 0.459604449490 - 0.009771253020*1j,
                                           -0.807028225834 + 0.009771253020*1j,
                                            0.347423776344 + 0.000000000000*1j],
                                          [-0.062303354995 - 0.062303354995*1j,
                                           -0.062303354995 - 0.062303354995*1j,
                                           -0.062303354995 - 0.062303354995*1j],
                                          [ 0.570587344099 - 0.000000000000*1j,
                                            0.570587344099 - 0.000000000000*1j,
                                            0.570587344099 + 0.000000000000*1j],
                                          [ 0.286272749085 + 0.286272749085*1j,
                                            0.286272749085 + 0.286272749085*1j,
                                           -0.572545498170 - 0.572545498170*1j],
                                          [ 0.052559422840 - 0.000000000000*1j,
                                            0.052559422840 + 0.000000000000*1j,
                                           -0.105118845679 + 0.000000000000*1j],
                                          [-0.459591797004 + 0.529611084985*1j,
                                            0.459591797004 - 0.529611084985*1j,
                                            0.000000000000 - 0.000000000000*1j],
                                          [ 0.006427739587 + 0.090808385909*1j,
                                           -0.006427739587 - 0.090808385909*1j,
                                            0.000000000000 + 0.000000000000*1j],
                                          [-0.403466180272 - 0.403466180272*1j,
                                           -0.403466180272 - 0.403466180272*1j,
                                           -0.403466180272 - 0.403466180272*1j],
                                          [-0.088110249616 - 0.000000000000*1j,
                                           -0.088110249616 - 0.000000000000*1j,
                                           -0.088110249616 + 0.000000000000*1j]],
                                         [[ 0.000000000000 + 0.000000000000*1j,
                                            0.031866260273 - 0.031866260273*1j,
                                           -0.031866260273 + 0.031866260273*1j],
                                          [-0.000000000000 - 0.000000000000*1j,
                                           -0.705669244698 + 0.000000000000*1j,
                                            0.705669244698 + 0.000000000000*1j],
                                          [-0.001780156891 + 0.001780156891*1j,
                                           -0.012680513033 + 0.012680513033*1j,
                                           -0.012680513033 + 0.012680513033*1j],
                                          [-0.582237273385 + 0.000000000000*1j,
                                            0.574608665929 - 0.000000000000*1j,
                                            0.574608665929 + 0.000000000000*1j],
                                          [-0.021184502078 + 0.021184502078*1j,
                                           -0.011544287510 + 0.011544287510*1j,
                                           -0.011544287510 + 0.011544287510*1j],
                                          [ 0.812686635458 - 0.000000000000*1j,
                                            0.411162853378 + 0.000000000000*1j,
                                            0.411162853378 + 0.000000000000*1j],
                                          [ 0.000000000000 + 0.000000000000*1j,
                                           -0.498983508201 + 0.498983508201*1j,
                                            0.498983508201 - 0.498983508201*1j],
                                          [ 0.000000000000 + 0.000000000000*1j,
                                           -0.045065697460 - 0.000000000000*1j,
                                            0.045065697460 + 0.000000000000*1j],
                                          [ 0.400389305548 - 0.400389305548*1j,
                                           -0.412005183792 + 0.412005183792*1j,
                                           -0.412005183792 + 0.412005183792*1j],
                                          [ 0.009657696420 - 0.000000000000*1j,
                                           -0.012050954709 + 0.000000000000*1j,
                                           -0.012050954709 + 0.000000000000*1j],
                                          [-0.582440084400 + 0.582440084400*1j,
                                           -0.282767859813 + 0.282767859813*1j,
                                           -0.282767859813 + 0.282767859813*1j],
                                          [-0.021140457173 + 0.000000000000*1j,
                                           -0.024995270201 - 0.000000000000*1j,
                                           -0.024995270201 + 0.000000000000*1j]]]

        NaH_phonon.expected_fermi = []
        self.NaH_phonon = NaH_phonon

    def test_cell_vec_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.cell_vec,
                               self.NaH_phonon.expected_cell_vec)

    def test_ion_pos_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.ion_pos,
                               self.NaH_phonon.expected_ion_pos)

    def test_ion_type_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.ion_type,
                               self.NaH_phonon.expected_ion_type)

    def test_kpts_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.kpts,
                               self.NaH_phonon.expected_kpts)

    def test_weights_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.weights,
                               self.NaH_phonon.expected_weights)

    def test_freqs_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.freqs,
                               self.NaH_phonon.expected_freqs)

    def test_freq_down_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.freq_down,
                               self.NaH_phonon.expected_freq_down)

    def test_eigenvecs_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.eigenvecs,
                               self.NaH_phonon.expected_eigenvecs)

    def test_fermi_read_nah_phonon(self):
        npt.assert_array_equal(self.NaH_phonon.fermi,
                               self.NaH_phonon.expected_fermi)


class TestReadInputFileFeBands(unittest.TestCase):

    def setUp(self):
        # Create trivial function object so attributes can be assigned to it
        Fe_bands = lambda:0
        # Need to use actual files here rather than simulating their content
        # with StringIO, in order to test the way the read_input_file function
        # searches for missing data (e.g. ion_pos) in other files
        Fe_bands_file = 'test/data/Fe.bands'
        units = 'hartree'
        up = False
        down = False
        ureg = UnitRegistry()

        with open(Fe_bands_file, 'r') as f:
            (Fe_bands.cell_vec, Fe_bands.ion_pos, Fe_bands.ion_type,
                Fe_bands.kpts, Fe_bands.weights, Fe_bands.freqs,
                Fe_bands.freq_down, Fe_bands.i_intens, Fe_bands.r_intens,
                Fe_bands.eigenvecs, Fe_bands.fermi) = read_input_file(
                    f, ureg, units, up, down)

        Fe_bands.expected_cell_vec = [[-2.708355,  2.708355,  2.708355],
                                      [ 2.708355, -2.708355,  2.708355],
                                      [ 2.708355,  2.708355, -2.708355]]

        Fe_bands.expected_ion_pos = []
        Fe_bands.expected_ion_type = []
        Fe_bands.expected_kpts = [[-0.37500000, -0.45833333,  0.29166667],
                                  [-0.37500000, -0.37500000,  0.29166667]]
        Fe_bands.expected_weights = [0.01388889, 0.01388889]
        Fe_bands.expected_freqs = [[0.02278248, 0.02644693, 0.12383402,
                                    0.15398152, 0.17125020, 0.43252010],
                                   [0.02760952, 0.02644911, 0.12442671,
                                    0.14597457, 0.16728951, 0.35463529]]
        Fe_bands.expected_freq_down = [[0.08112495, 0.08345039, 0.19185076,
                                        0.22763689, 0.24912308, 0.46511567],
                                       [0.08778721, 0.08033338, 0.19288937,
                                        0.21817779, 0.24476910, 0.39214129]]
        Fe_bands.expected_fermi = [0.173319, 0.173319]
        self.Fe_bands = Fe_bands

    def test_cell_vec_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.cell_vec,
                               self.Fe_bands.expected_cell_vec)

    def test_ion_pos_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.ion_pos,
                               self.Fe_bands.expected_ion_pos)

    def test_ion_type_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.ion_type,
                               self.Fe_bands.expected_ion_type)

    def test_kpts_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.kpts,
                               self.Fe_bands.expected_kpts)

    def test_weights_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.weights,
                               self.Fe_bands.expected_weights)

    def test_freqs_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.freqs,
                               self.Fe_bands.expected_freqs)

    def test_freq_down_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.freq_down,
                               self.Fe_bands.expected_freq_down)

    def test_eigenvecs_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.eigenvecs, [])

    def test_fermi_read_fe_bands(self):
        npt.assert_array_equal(self.Fe_bands.fermi,
                               self.Fe_bands.expected_fermi)


class TestReadDotPhononAndHeader(unittest.TestCase):

    def setUp(self):
        self.ureg = UnitRegistry()
        # Create trivial function object so attributes can be assigned to it
        NaH = lambda:0
        NaH.content = '\n'.join([
           u' BEGIN header',
            ' Number of ions         2',
            ' Number of branches     6',
            ' Number of wavevectors  2',
            ' Frequencies in         cm-1',
            ' IR intensities in      (D/A)**2/amu',
            ' Raman activities in    A**4 amu**(-1)',
            ' Unit cell vectors (A)',
            '    0.000000    2.399500    2.399500',
            '    2.399500    0.000000    2.399500',
            '    2.399500    2.399500    0.000000',
            ' Fractional Co-ordinates',
            '     1     0.500000    0.500000    0.500000   H         1.007940',
            '     2     0.000000    0.000000    0.000000   Na       22.989770',
            ' END header',
            '     q-pt=    1   -0.250000 -0.250000 -0.250000      0.1250000000',
            '       1      91.847109',
            '       2      91.847109',
            '       3     166.053018',
            '       4     564.508299',
            '       5     564.508299',
            '       6     884.068976',
            '                        Phonon Eigenvectors',
            'Mode Ion                X                                   Y                                   Z',
            '   1   1 -0.061613336996 -0.060761142686     -0.005526816216 -0.006379010526      0.067140153211  0.067140153211',
            '   1   2  0.666530886823 -0.004641603630      0.064846864124  0.004641603630     -0.731377750947  0.000000000000',
            '   2   1 -0.043088481348 -0.041294487960      0.074981829953  0.073187836565     -0.031893348605 -0.031893348605',
            '   2   2  0.459604449490 -0.009771253020     -0.807028225834  0.009771253020      0.347423776344  0.000000000000',
            '   3   1 -0.062303354995 -0.062303354995     -0.062303354995 -0.062303354995     -0.062303354995 -0.062303354995',
            '   3   2  0.570587344099 -0.000000000000      0.570587344099 -0.000000000000      0.570587344099  0.000000000000',
            '   4   1  0.286272749085  0.286272749085      0.286272749085  0.286272749085     -0.572545498170 -0.572545498170',
            '   4   2  0.052559422840 -0.000000000000      0.052559422840  0.000000000000     -0.105118845679  0.000000000000',
            '   5   1 -0.459591797004  0.529611084985      0.459591797004 -0.529611084985      0.000000000000 -0.000000000000',
            '   5   2  0.006427739587  0.090808385909     -0.006427739587 -0.090808385909      0.000000000000  0.000000000000',
            '   6   1 -0.403466180272 -0.403466180272     -0.403466180272 -0.403466180272     -0.403466180272 -0.403466180272',
            '   6   2 -0.088110249616 -0.000000000000     -0.088110249616 -0.000000000000     -0.088110249616  0.000000000000',
            '     q-pt=    2   -0.250000 -0.500000 -0.500000      0.3750000000',
            '       1     132.031513',
            '       2     154.825631',
            '       3     206.213940',
            '       4     642.513551',
            '       5     690.303338',
            '       6     832.120011',
            '                        Phonon Eigenvectors',
            'Mode Ion                X                                   Y                                   Z',
            '   1   1  0.000000000000  0.000000000000      0.031866260273 -0.031866260273     -0.031866260273  0.031866260273',
            '   1   2 -0.000000000000 -0.000000000000     -0.705669244698  0.000000000000      0.705669244698  0.000000000000',
            '   2   1 -0.001780156891  0.001780156891     -0.012680513033  0.012680513033     -0.012680513033  0.012680513033',
            '   2   2 -0.582237273385  0.000000000000      0.574608665929 -0.000000000000      0.574608665929  0.000000000000',
            '   3   1 -0.021184502078  0.021184502078     -0.011544287510  0.011544287510     -0.011544287510  0.011544287510',
            '   3   2  0.812686635458 -0.000000000000      0.411162853378  0.000000000000      0.411162853378  0.000000000000',
            '   4   1  0.000000000000  0.000000000000     -0.498983508201  0.498983508201      0.498983508201 -0.498983508201',
            '   4   2  0.000000000000  0.000000000000     -0.045065697460 -0.000000000000      0.045065697460  0.000000000000',
            '   5   1  0.400389305548 -0.400389305548     -0.412005183792  0.412005183792     -0.412005183792  0.412005183792',
            '   5   2  0.009657696420 -0.000000000000     -0.012050954709  0.000000000000     -0.012050954709  0.000000000000',
            '   6   1 -0.582440084400  0.582440084400     -0.282767859813  0.282767859813     -0.282767859813  0.282767859813',
            '   6   2 -0.021140457173  0.000000000000     -0.024995270201 -0.000000000000     -0.024995270201  0.000000000000'
            ])
        NaH.expected_n_ions = 2
        NaH.expected_n_branches = 6
        NaH.expected_n_qpts = 2
        NaH.expected_cell_vec = [[0.000000, 2.399500, 2.399500],
                                 [2.399500, 0.000000, 2.399500],
                                 [2.399500, 2.399500, 0.000000]]
        NaH.expected_ion_pos = [[0.500000, 0.500000, 0.500000],
                                 [0.000000, 0.000000, 0.000000]]
        NaH.expected_ion_type = ['H', 'Na']
        NaH.expected_qpts = [[-0.250000, -0.250000, -0.250000],
                             [-0.250000, -0.500000, -0.500000]]
        NaH.expected_weights = [0.125, 0.375]
        NaH.expected_freqs = [[91.847109, 91.847109, 166.053018,
                               564.508299, 564.508299, 884.068976],
                              [132.031513, 154.825631, 206.213940,
                               642.513551, 690.303338, 832.120011]]
        NaH.expected_eigenvecs = [[[-0.061613336996 - 0.060761142686*1j,
                                    -0.005526816216 - 0.006379010526*1j,
                                     0.067140153211 + 0.067140153211*1j],
                                   [ 0.666530886823 - 0.004641603630*1j,
                                     0.064846864124 + 0.004641603630*1j,
                                    -0.731377750947 + 0.000000000000*1j],
                                   [-0.043088481348 - 0.041294487960*1j,
                                     0.074981829953 + 0.073187836565*1j,
                                    -0.031893348605 - 0.031893348605*1j],
                                   [ 0.459604449490 - 0.009771253020*1j,
                                    -0.807028225834 + 0.009771253020*1j,
                                     0.347423776344 + 0.000000000000*1j],
                                   [-0.062303354995 - 0.062303354995*1j,
                                    -0.062303354995 - 0.062303354995*1j,
                                    -0.062303354995 - 0.062303354995*1j],
                                   [ 0.570587344099 - 0.000000000000*1j,
                                     0.570587344099 - 0.000000000000*1j,
                                     0.570587344099 + 0.000000000000*1j],
                                   [ 0.286272749085 + 0.286272749085*1j,
                                     0.286272749085 + 0.286272749085*1j,
                                    -0.572545498170 - 0.572545498170*1j],
                                   [ 0.052559422840 - 0.000000000000*1j,
                                     0.052559422840 + 0.000000000000*1j,
                                    -0.105118845679 + 0.000000000000*1j],
                                   [-0.459591797004 + 0.529611084985*1j,
                                     0.459591797004 - 0.529611084985*1j,
                                     0.000000000000 - 0.000000000000*1j],
                                   [ 0.006427739587 + 0.090808385909*1j,
                                    -0.006427739587 - 0.090808385909*1j,
                                     0.000000000000 + 0.000000000000*1j],
                                   [-0.403466180272 - 0.403466180272*1j,
                                    -0.403466180272 - 0.403466180272*1j,
                                    -0.403466180272 - 0.403466180272*1j],
                                   [-0.088110249616 - 0.000000000000*1j,
                                    -0.088110249616 - 0.000000000000*1j,
                                    -0.088110249616 + 0.000000000000*1j]],
                                  [[ 0.000000000000 + 0.000000000000*1j,
                                     0.031866260273 - 0.031866260273*1j,
                                    -0.031866260273 + 0.031866260273*1j],
                                   [-0.000000000000 - 0.000000000000*1j,
                                    -0.705669244698 + 0.000000000000*1j,
                                     0.705669244698 + 0.000000000000*1j],
                                   [-0.001780156891 + 0.001780156891*1j,
                                    -0.012680513033 + 0.012680513033*1j,
                                    -0.012680513033 + 0.012680513033*1j],
                                   [-0.582237273385 + 0.000000000000*1j,
                                     0.574608665929 - 0.000000000000*1j,
                                     0.574608665929 + 0.000000000000*1j],
                                   [-0.021184502078 + 0.021184502078*1j,
                                    -0.011544287510 + 0.011544287510*1j,
                                    -0.011544287510 + 0.011544287510*1j],
                                   [ 0.812686635458 - 0.000000000000*1j,
                                     0.411162853378 + 0.000000000000*1j,
                                     0.411162853378 + 0.000000000000*1j],
                                   [ 0.000000000000 + 0.000000000000*1j,
                                    -0.498983508201 + 0.498983508201*1j,
                                     0.498983508201 - 0.498983508201*1j],
                                   [ 0.000000000000 + 0.000000000000*1j,
                                    -0.045065697460 - 0.000000000000*1j,
                                     0.045065697460 + 0.000000000000*1j],
                                   [ 0.400389305548 - 0.400389305548*1j,
                                    -0.412005183792 + 0.412005183792*1j,
                                    -0.412005183792 + 0.412005183792*1j],
                                   [ 0.009657696420 - 0.000000000000*1j,
                                    -0.012050954709 + 0.000000000000*1j,
                                    -0.012050954709 + 0.000000000000*1j],
                                   [-0.582440084400 + 0.582440084400*1j,
                                    -0.282767859813 + 0.282767859813*1j,
                                    -0.282767859813 + 0.282767859813*1j],
                                   [-0.021140457173 + 0.000000000000*1j,
                                    -0.024995270201 - 0.000000000000*1j,
                                    -0.024995270201 + 0.000000000000*1j]]]
        (NaH.n_ions, NaH.n_branches, NaH.n_qpts, NaH.cell_vec, NaH.ion_pos,
            NaH.ion_type) = read_dot_phonon_header(StringIO(NaH.content))
        (NaH.cell_vec_file, NaH.ion_pos_file, NaH.ion_type_file, NaH.qpts,
            NaH.weights, NaH.freqs, NaH.i_intens, NaH.r_intens,
            NaH.eigenvecs) = read_dot_phonon(
                StringIO(NaH.content), self.ureg, read_eigenvecs=True)
        self.NaH = NaH

    def test_n_ions_read_nah(self):
        self.assertEqual(self.NaH.n_ions, self.NaH.expected_n_ions)

    def test_n_branches_read_nah(self):
        self.assertEqual(self.NaH.n_branches, self.NaH.expected_n_branches)

    def test_cell_vec_read_nah(self):
        npt.assert_array_equal(self.NaH.cell_vec, self.NaH.expected_cell_vec)

    def test_ion_pos_read_nah(self):
        npt.assert_array_equal(self.NaH.ion_pos, self.NaH.expected_ion_pos)

    def test_ion_type_read_nah(self):
        npt.assert_array_equal(self.NaH.ion_type, self.NaH.expected_ion_type)

    def test_n_qpts_read_nah(self):
        self.assertEqual(self.NaH.n_qpts, self.NaH.expected_n_qpts)

    def test_qpts_read_nah(self):
        npt.assert_array_equal(self.NaH.qpts, self.NaH.expected_qpts)

    def test_weights_read_nah(self):
        npt.assert_array_equal(self.NaH.weights, self.NaH.expected_weights)

    def test_freqs_read_nah(self):
        npt.assert_array_equal(self.NaH.freqs, self.NaH.expected_freqs)

    def test_eigenvecs_read_nah(self):
        npt.assert_array_equal(self.NaH.eigenvecs, self.NaH.expected_eigenvecs)

    def test_cell_vec_file_read_nah(self):
        npt.assert_array_equal(self.NaH.cell_vec_file, self.NaH.expected_cell_vec)

    def test_ion_pos_file_read_nah(self):
        npt.assert_array_equal(self.NaH.ion_pos_file, self.NaH.expected_ion_pos)

    def test_ion_type_file_read_nah(self):
        npt.assert_array_equal(self.NaH.ion_type_file, self.NaH.expected_ion_type)


class TestReadDotBands(unittest.TestCase):

    def setUp(self):
        self.ureg = UnitRegistry()
        # Create trivial function object so attributes can be assigned to it
        iron = lambda:0
        iron.content = '\n'.join([
           u'Number of k-points   2',
            'Number of spin components 2',
            'Number of electrons  4.500     3.500',
            'Number of eigenvalues      6     6',
            'Fermi energies (in atomic units)     0.173319    0.173319',
            'Unit cell vectors',
            '   -2.708355    2.708355    2.708355',
            '    2.708355   -2.708355    2.708355',
            '    2.708355    2.708355   -2.708355',
            'K-point    1 -0.37500000 -0.45833333  0.29166667  0.01388889',
            'Spin component 1',
            '    0.02278248',
            '    0.02644693',
            '    0.12383402',
            '    0.15398152',
            '    0.17125020',
            '    0.43252010',
            'Spin component 2',
            '    0.08112495',
            '    0.08345039',
            '    0.19185076',
            '    0.22763689',
            '    0.24912308',
            '    0.46511567',
            'K-point    2 -0.37500000 -0.37500000  0.29166667  0.01388889',
            'Spin component 1',
            '    0.02760952',
            '    0.02644911',
            '    0.12442671',
            '    0.14597457',
            '    0.16728951',
            '    0.35463529',
            'Spin component 2',
            '    0.08778721',
            '    0.08033338',
            '    0.19288937',
            '    0.21817779',
            '    0.24476910',
            '    0.39214129'
        ])
        iron.expected_fermi = [0.173319, 0.173319]
        iron.expected_cell_vec = [[-2.708355,  2.708355,  2.708355],
                                  [ 2.708355, -2.708355,  2.708355],
                                  [ 2.708355,  2.708355, -2.708355]]
        iron.expected_kpts = [[-0.37500000, -0.45833333,  0.29166667],
                              [-0.37500000, -0.37500000,  0.29166667]]
        iron.expected_weights = [0.01388889, 0.01388889]
        iron.expected_freq_up = [[0.02278248, 0.02644693, 0.12383402,
                                  0.15398152, 0.17125020, 0.43252010],
                                 [0.02760952, 0.02644911, 0.12442671,
                                  0.14597457, 0.16728951, 0.35463529]]
        iron.expected_freq_down = [[0.08112495, 0.08345039, 0.19185076,
                                    0.22763689, 0.24912308, 0.46511567],
                                   [0.08778721, 0.08033338, 0.19288937,
                                    0.21817779, 0.24476910, 0.39214129]]
        (iron.fermi, iron.cell_vec, iron.kpts, iron.weights, iron.freq_up,
            iron.freq_down) = read_dot_bands(
                StringIO(iron.content), self.ureg, False, False,
                units='hartree')
        self.iron = iron

    def test_freq_up_read_iron(self):
        npt.assert_array_equal(self.iron.freq_up, self.iron.expected_freq_up)

    def test_freq_down_read_iron(self):
        npt.assert_array_equal(self.iron.freq_down, self.iron.expected_freq_down)

    def test_kpts_read_iron(self):
        npt.assert_array_equal(self.iron.kpts, self.iron.expected_kpts)

    def test_fermi_read_iron(self):
        npt.assert_array_equal(self.iron.fermi, self.iron.expected_fermi)

    def test_weights_read_iron(self):
        npt.assert_array_equal(self.iron.weights, self.iron.expected_weights)

    def test_cell_vec_read_iron(self):
        npt.assert_array_equal(self.iron.cell_vec, self.iron.expected_cell_vec)

    def test_up_arg_freq_up_read_iron(self):
        freq_up = read_dot_bands(
            StringIO(self.iron.content), self.ureg, True, False,
            units='hartree')[4]
        npt.assert_array_equal(freq_up, self.iron.expected_freq_up)

    def test_up_arg_freq_down_read_iron(self):
        freq_down = read_dot_bands(
            StringIO(self.iron.content), self.ureg, True, False,
            units='hartree')[5]
        self.assertEqual(freq_down.size, 0)

    def test_down_arg_freq_up_read_iron(self):
        freq_up = read_dot_bands(
            StringIO(self.iron.content), self.ureg, False, True,
            units='hartree')[4]
        self.assertEqual(freq_up.size, 0)

    def test_down_arg_freq_down_read_iron(self):
        freq_down = read_dot_bands(
            StringIO(self.iron.content), self.ureg, False, True,
            units='hartree')[5]
        npt.assert_array_equal(freq_down, self.iron.expected_freq_down)

    def test_freq_up_cm_units_iron(self):
        freq_up_cm = read_dot_bands(
            StringIO(self.iron.content), self.ureg, units='1/cm')[4]
        expected_freq_up_cm = [[5000.17594, 5804.429679, 27178.423392,
                                33795.034234, 37585.071062, 94927.180782],
                               [6059.588667, 5804.908134, 27308.5038,
                                32037.711995, 36715.800165, 77833.44239]]
        npt.assert_allclose(freq_up_cm, expected_freq_up_cm)

    def test_freq_down_cm_units_iron(self):
        freq_down_cm = read_dot_bands(
            StringIO(self.iron.content), self.ureg, units='1/cm')[5]
        expected_freq_down_cm = [[17804.86686, 18315.2419, 42106.370959,
                                  49960.517927, 54676.191123, 102081.080835],
                                 [19267.063783, 17631.137342, 42334.319485,
                                  47884.485632, 53720.603056, 86065.057157]]
        npt.assert_allclose(freq_down_cm, expected_freq_down_cm)
