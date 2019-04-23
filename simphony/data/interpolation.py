import math
import struct
import sys
import os
import warnings
import numpy as np
from scipy.linalg.lapack import zheev
from scipy.special import erfc
from simphony import ureg
from simphony.util import reciprocal_lattice, is_gamma
from simphony.data.data import Data


class InterpolationData(Data):
    """
    A class to read the data required for a supercell phonon interpolation
    calculation from a .castep_bin file, and store any calculated
    frequencies/eigenvectors

    Attributes
    ----------
    seedname : str
        Seedname specifying castep_bin file to read from
    n_ions : int
        Number of ions in the unit cell
    n_branches : int
        Number of phonon dispersion branches
    cell_vec : ndarray
        The unit cell vectors. Default units Angstroms.
        dtype = 'float'
        shape = (3, 3)
    n_ions_in_species : ndarray
        The number of ions in each species, in the same order as the species
        in ion_type
        shape = (n_species,)
    ion_r : ndarray
        The fractional position of each ion within the unit cell
        dtype = 'float'
        shape = (n_ions, 3)
    ion_type : ndarray
        The chemical symbols of each ion in the unit cell. Ions are in the
        same order as in ion_r
        dtype = 'string'
        shape = (n_ions,)
    ion_mass : ndarray
        The mass of each ion in the unit cell in atomic units
        dtype = 'float'
        shape = (n_ions,)
    n_cells_in_sc : int
        Number of cells in the supercell
    sc_matrix : ndarray
        The supercell matrix
        dtype = 'int'
        shape = (3, 3)
    cell_origins : ndarray
        The locations of the unit cells within the supercell
        dtype = 'int'
        shape = (n_cells_in_sc, 3)
    force_constants : ndarray
        Force constants matrix. Default units atomic units
        dtype = 'float'
        shape = (n_cells_in_sc, 3*n_ions, 3*n_ions)
    n_qpts : int
        Number of q-points used in the most recent interpolation calculation.
        Default value 0
    qpts : ndarray
        Coordinates of the q-points used for the most recent interpolation
        calculation. Is empty by default
        dtype = 'float'
        shape = (n_qpts, 3)
    weights : ndarray
        The weight for each q-point
        dtype = 'float'
        shape = (n_qpts,)
    freqs: ndarray
        Phonon frequencies from the most recent interpolation calculation.
        Default units meV. Is empty by default
        dtype = 'float'
        shape = (n_qpts, 3*n_ions)
    eigenvecs: ndarray
        Dynamical matrix eigenvectors from the most recent interpolation
        calculation. Is empty by default
        dtype = 'complex'
        shape = (n_qpts, 3*n_ions, n_ions, 3)
    n_gamma_pts : ndarray
    n_sc_images : ndarray
        The number or periodic supercell images for each displacement of ion i
        in the unit cell and ion j in the supercell. This attribute doesn't
        exist until calculate_fine_phonons has been called
        dtype = 'int'
        shape = (n_cells_in_sc, n_ions, n_ions)
    max_sc_images : int
        The maximum number of periodic supercell images over all ij
        displacements. This is required for efficiency when summing phases
        over all images, so we only have to sum up to the maximum *actual*
        images, not up to the maximum possible images
    sc_image_i : ndarray
        The index describing the supercell each of the periodic images resides
        in. This is the index of the list of supercells as returned by
        _get_all_origins. This attribute doesn't exist until
        calculate_fine_phonons has been called
        dtype = 'int'
        shape = (n_cells_in_sc, n_ions, n_ions, (2*lim + 1)**3)
    force_constants_asr : ndarray
        Force constants matrix that has the acoustic sum rule applied. This
        attribute doesn't exist until calculate_fine_phonons has been called
        with asr=True. Default units atomic units
        dtype = 'float'
        shape = (n_cells_in_sc, 3*n_ions, 3*n_ions)
    asr : boolean
        Stores whether the acoustic sum rule was used in the last phonon
        calculation. Ensures consistency of other calculations e.g. when
        calculating on a grid of phonons for the Debye-Waller factor
    dipole : boolean
        Stores whether the Ewald dipole tail correction was used in the last
        phonon calculation. Ensures consistency of other calculations e.g.
        when calculating on a grid of phonons for the Debye-Waller factor
    split_i : ndarray
        The q-point indices where there is LO-TO splitting, if applicable.
        Otherwise empty.
        dtype = 'int'
        shape = (n_splits,)
    split_freqs : ndarray
        Holds the additional LO-TO split phonon frequencies for the q-points
        specified in split_i. Empty if no LO-TO splitting. Default units meV
        dtype = 'float'
        shape = (n_splits, 3*n_ions)
    split_eigenvecs : ndarray
        Holds the additional LO-TO split dynamical matrix eigenvectors for the
        q-points specified in split_i. Empty if no LO-TO splitting
        dtype = 'complex'
        shape = (n_splits, 3*n_ions, n_ions, 3)

    """

    def __init__(self, seedname, path='', qpts=np.array([])):
        """"
        Reads .castep_bin file, sets attributes, and calculates
        frequencies/eigenvectors at specific q-points if requested

        Parameters
        ----------
        seedname : str
            Name of .castep_bin file to read
        path : str, optional
            Path to dir containing the .castep_bin file, if it is in another 
            directory
        qpts : ndarray, optional
            Q-point coordinates to use for an initial interpolation calculation
            dtype = 'float'
            shape = (n_qpts, 3)
        """
        self._get_data(seedname, path)

        self.seedname = seedname
        self.qpts = qpts
        self.n_qpts = 0
        self.eigenvecs = np.array([])
        self.freqs = np.array([])*ureg.meV

        self.split_i = np.array([], dtype=np.int32)
        self.split_eigenvecs = np.array([])
        self.split_freqs = np.array([])*ureg.meV

        if self.n_qpts > 0:
            self.calculate_fine_phonons(qpts)


    def _get_data(self, seedname, path):
        """"
        Opens .castep_bin file for reading

        Parameters
        ----------
        seedname : str
            Name of .castep_bin file to read
        path : str
            Path to dir containing the .castep_bin file, if it is in another 
            directory
        """
        try:
            file = os.path.join(path, seedname + '.castep_bin')
            with open(file, 'rb') as f:
                self._read_interpolation_data(f)
        except IOError:
           file = os.path.join(path, seedname + '.check')
           with open(file, 'rb') as f:
               self._read_interpolation_data(f)


    def _read_interpolation_data(self, file_obj):
        """
        Reads data from .castep_bin file and sets attributes

        Parameters
        ----------
        f : file object
            File object in read mode for the .castep_bin file containing the
            data
        """

        def read_entry(file_obj, dtype=''):
            """
            Read a record from a Fortran binary file, including the beginning
            and end record markers and the data inbetween
            """
            def record_mark_read(file_obj):
                # Read 4 byte Fortran record marker
                return struct.unpack('>i', file_obj.read(4))[0]

            begin = record_mark_read(file_obj)
            if dtype:
                n_bytes = int(dtype[-1])
                n_elems = int(begin/n_bytes)
                if n_elems > 1:
                    data = np.fromfile(file_obj, dtype=dtype, count=n_elems)
                else:
                    if 'i' in dtype:
                        data = struct.unpack('>i', file_obj.read(begin))[0]
                    elif 'f' in dtype:
                        data = struct.unpack('>d', file_obj.read(begin))[0]
                    else:
                        data = file_obj.read(begin)
            else:
                data = file_obj.read(begin)
            end = record_mark_read(file_obj)
            if begin != end:
                sys.exit("""Problem reading binary file: beginning and end
                            record markers do not match""")

            return data

        int_type = '>i4'
        float_type = '>f8'

        header = ''
        while header.strip() != b'END':
            header = read_entry(file_obj)
            if header.strip() == b'CELL%NUM_IONS':
                n_ions = read_entry(file_obj, int_type)
            elif header.strip() == b'CELL%REAL_LATTICE':
                cell_vec = np.transpose(np.reshape(
                    read_entry(file_obj, float_type), (3, 3)))
            elif header.strip() == b'CELL%NUM_SPECIES':
                n_species = read_entry(file_obj, int_type)
            elif header.strip() == b'CELL%NUM_IONS_IN_SPECIES':
                n_ions_in_species = read_entry(file_obj, int_type)
                if n_species == 1:
                    n_ions_in_species = np.array([n_ions_in_species])
            elif header.strip() == b'CELL%IONIC_POSITIONS':
                max_ions_in_species = max(n_ions_in_species)
                ion_r_tmp = np.reshape(read_entry(file_obj, float_type),
                                  (n_species, max_ions_in_species, 3))
            elif header.strip() == b'CELL%SPECIES_MASS':
                ion_mass_tmp = read_entry(file_obj, float_type)
                if n_species == 1:
                    ion_mass_tmp = np.array([ion_mass_tmp])
            elif header.strip() == b'CELL%SPECIES_SYMBOL':
                # Need to decode binary string for Python 3 compatibility
                if n_species == 1:
                    ion_type_tmp = [read_entry(file_obj, 'S8').strip().decode('utf-8')]
                else:
                    ion_type_tmp = [x.strip().decode('utf-8') for x in read_entry(file_obj, 'S8')]
            elif header.strip() == b'FORCE_CON':
                sc_matrix = np.transpose(np.reshape(
                    read_entry(file_obj, int_type), (3, 3)))
                n_cells_in_sc = int(np.rint(np.absolute(
                    np.linalg.det(sc_matrix))))
                force_constants = np.reshape(read_entry(file_obj, float_type),
                                    (n_cells_in_sc, 3*n_ions, 3*n_ions))
                cell_origins = np.reshape(
                    read_entry(file_obj, int_type), (n_cells_in_sc, 3))
                fc_row = read_entry(file_obj, int_type)
            elif header.strip() == b'BORN_CHGS':
                born = np.reshape(read_entry(file_obj, float_type), (n_ions, 3, 3))
            elif header.strip() == b'DIELECTRIC':
                dielectric = np.transpose(np.reshape(
                    read_entry(file_obj, float_type), (3, 3)))

        # Get ion_r in correct form
        # CASTEP stores ion positions as 3D array (3,
        # max_ions_in_species, n_species) so need to slice data to get
        # correct information
        ion_begin = np.insert(np.cumsum(n_ions_in_species[:-1]), 0, 0)
        ion_end = np.cumsum(n_ions_in_species)
        ion_r = np.zeros((n_ions, 3))
        for i in range(n_species):
                ion_r[ion_begin[i]:ion_end[i], :] = ion_r_tmp[
                    i,:n_ions_in_species[i], :]
        # Get ion_type in correct form
        ion_type = np.array([])
        ion_mass = np.array([])
        for ion in range(n_species):
            ion_type = np.append(ion_type, [ion_type_tmp[ion] for i in
                range(n_ions_in_species[ion])])
            ion_mass = np.append(ion_mass, [ion_mass_tmp[ion] for i in
                range(n_ions_in_species[ion])])

        cell_vec = cell_vec*ureg.bohr
        cell_vec.ito('angstrom')
        ion_mass = ion_mass*ureg.e_mass
        ion_mass.ito('amu')

        self.n_ions = n_ions
        self.n_branches = 3*n_ions
        self.cell_vec = cell_vec
        self.n_ions_in_species = n_ions_in_species
        self.ion_r = ion_r - np.floor(ion_r) # Normalise ion coordinates
        self.ion_type = ion_type
        self.ion_mass = ion_mass

        # Set attributes relating to 'FORCE_CON' block
        try:
            force_constants = force_constants*ureg.hartree/(ureg.bohr**2)
            self.force_constants = force_constants
            self.sc_matrix = sc_matrix
            self.n_cells_in_sc = n_cells_in_sc
            self.cell_origins = cell_origins
        except UnboundLocalError:
            sys.exit(('Error: force constants matrix could not be found in '
                      '{:s}\n').format(file_obj.name))

         # Set attributes relating to dipoles
        try:
            self.born = born*ureg.e
            self.dielectric = dielectric
        except UnboundLocalError:
            pass


    def calculate_fine_phonons(self, qpts, asr=None, precondition=False,
                               set_attrs=True, dipole=True, splitting=True):
        """
        Calculate phonon frequencies and eigenvectors at specified q-points
        from a supercell force constant matrix via interpolation. For more
        information on the method see section 2.5:
        http://www.tcm.phy.cam.ac.uk/castep/Phonons_Guide/Castep_Phonons.html

        Parameters
        ----------
        qpts : ndarray
            The q-points to interpolate onto
            dtype = 'float'
            shape = (n_qpts, 3)
        asr : {'realspace', 'reciprocal'}, optional, default None
            Which acoustic sum rule correction to apply. 'realspace' applies
            the correction to the force constant matrix in real space.
            'reciprocal' applies the correction to the dynamical matrix at
            every q-point
        precondition : boolean, optional, default False
            Whether to precondition the dynamical matrix using the
            eigenvectors from the previous q-point
        set_attrs : boolean, optional, default True
            Whether to set the freqs, eigenvecs, qpts and n_qpts attributes of
            the InterpolationData object to the newly calculated values
        dipole : boolean, optional, default True
            Calculates the dipole tail correction to the dynamical matrix at
            each q-point using the Ewald sum, if the Born charges and
            dielectric permitivitty tensor are present.
        splitting : boolean, optional, default True
            Whether to calculate the LO-TO splitting at the gamma points. Only
            applied if dipole is True and the Born charges and dielectric
            permitivitty tensor are present.

        Returns
        -------
        freqs : ndarray
            The phonon frequencies (same as set to InterpolationData.freqs)
            dtype = 'float'
            shape = (n_qpts, 3*n_ions)
        eigenvecs : ndarray
            The phonon eigenvectors (same as set to
            InterpolationData.eigenvecs)
            dtype = 'complex'
            shape = (n_qpts, 3*n_ions, n_ions, 3)
        """
        self.dyn_mats = np.zeros((len(qpts), 3*self.n_ions, 3*self.n_ions), dtype=np.complex128)
        if asr == 'realspace':
            if not hasattr(self, 'force_constants_asr'):
                self.force_constants_asr = self._enforce_realspace_asr()
            force_constants = self.force_constants_asr.magnitude
        else:
            force_constants = self.force_constants.magnitude

        if not hasattr(self, 'born') or not hasattr(self, 'dielectric'):
            dipole = False
        if not dipole:
            splitting = False

        if dipole and not hasattr(self, 'eta'):
            self._dipole_correction_init()

        ion_mass = self.ion_mass.to('e_mass').magnitude
        sc_matrix = self.sc_matrix
        cell_origins = self.cell_origins
        n_cells_in_sc = self.n_cells_in_sc
        n_ions = self.n_ions
        n_branches = self.n_branches
        n_qpts = len(qpts)
        freqs = np.zeros((n_qpts, n_branches))
        freqs_test = np.zeros((n_qpts, n_branches))
        eigenvecs = np.zeros((n_qpts, n_branches, n_ions, 3),
                             dtype=np.complex128)
        split_i = np.array([], dtype=np.int32)
        split_freqs = np.empty((0, n_branches))
        split_eigenvecs = np.empty((0, n_branches, n_ions, 3))

        # Build list of all possible supercell image coordinates
        lim = 2 # Supercell image limit
        sc_image_r = self._get_all_origins(
            np.repeat(lim, 3) + 1, min_xyz=-np.repeat(lim, 3))
        # Get a list of all the unique supercell image origins and cell origins
        # in x, y, z and how to rebuild them to minimise expensive phase
        # calculations later
        sc_offsets = np.einsum('ji,kj->ki', sc_matrix, sc_image_r)
        unique_sc_offsets = [[] for i in range(3)]
        unique_sc_i = np.zeros((len(sc_offsets), 3), dtype=np.int32)
        unique_cell_origins = [[] for i in range(3)]
        unique_cell_i = np.zeros((len(cell_origins), 3), dtype=np.int32)
        for i in range(3):
            unique_sc_offsets[i], unique_sc_i[:, i] = np.unique(
                sc_offsets[:, i], return_inverse=True)
            unique_cell_origins[i], unique_cell_i[:, i] = np.unique(
                self.cell_origins[:, i], return_inverse=True)


        # Construct list of supercell ion images
        if not hasattr(self, 'sc_image_i'):
            self._calculate_supercell_images(lim)
        n_sc_images = self.n_sc_images
        max_sc_images = self.max_sc_images
        sc_image_i = self.sc_image_i

        # Precompute fc matrix weighted by number of supercell ion images
        # (for cumulant method)
        n_sc_images_repeat = np.transpose(
            n_sc_images.repeat(3, axis=2).repeat(3, axis=1), axes=[0,2,1])
        fc_img_weighted = np.divide(
            force_constants, n_sc_images_repeat, where=n_sc_images_repeat != 0)

        # Precompute dynamical matrix mass weighting
        masses = np.tile(np.repeat(ion_mass, 3), (3*n_ions, 1))
        dyn_mat_weighting = 1/np.sqrt(masses*np.transpose(masses))

        if asr == 'reciprocal':
            q_gamma = np.array([0., 0., 0.])
            dyn_mat_gamma = self._calculate_dyn_mat(
                q_gamma, fc_img_weighted, unique_sc_offsets,
                unique_sc_i, unique_cell_origins, unique_cell_i)
            if dipole:
                dyn_mat_gamma += self._calculate_dipole_correction(q_gamma)

        prev_evecs = np.identity(3*n_ions)
        for q in range(n_qpts):
            qpt = qpts[q, :]

            dyn_mat = self._calculate_dyn_mat(
                qpt, fc_img_weighted, unique_sc_offsets, unique_sc_i,
                unique_cell_origins, unique_cell_i)

            if dipole:
                dipole_corr = self._calculate_dipole_correction(qpt)
                dyn_mat += dipole_corr

            if asr == 'reciprocal':
                dyn_mat = self._enforce_reciprocal_asr(dyn_mat_gamma, dyn_mat)

            # Calculate LO-TO splitting by calculating non-analytic correction
            # to dynamical matrix
            if splitting and is_gamma(qpt):
                if q == 0:
                    q_dirs = [qpts[1]]
                elif q == (n_qpts - 1):
                    q_dirs = [qpts[-2]]
                else:
                    q_dirs = [-qpts[q - 1], qpts[q + 1]]
                na_corrs = np.zeros((len(q_dirs), 3*n_ions, 3*n_ions),
                                    dtype=np.complex128)
                for i, q_dir in enumerate(q_dirs):
                    na_corrs[i] = self._calculate_gamma_correction(q_dir)
            else:
            # Correction is zero if not a gamma point or splitting = False
                na_corrs = np.array([0])

            for i, na_corr in enumerate(na_corrs):
                dyn_mat_corr = dyn_mat + na_corr

                # Mass weight dynamical matrix
                dyn_mat_corr *= dyn_mat_weighting

                if precondition:
                    dyn_mat_corr = np.matmul(np.matmul(np.transpose(
                        np.conj(prev_evecs)), dyn_mat_corr), prev_evecs)

                try:
                    evals, evecs = np.linalg.eigh(dyn_mat_corr)
                # Fall back to zheev if eigh fails (eigh calls zheevd)
                except np.linalg.LinAlgError:
                    evals, evecs, info = zheev(dyn_mat_corr)
                self.dyn_mats[q] = dyn_mat_corr
                prev_evecs = evecs
                evecs = np.reshape(np.transpose(evecs), (n_branches, n_ions, 3))
                # Set imaginary frequencies to negative
                imag_freqs = np.where(evals < 0)
                evals = np.sqrt(np.abs(evals))
                evals[imag_freqs] *= -1

                if i == 0:
                    eigenvecs[q, :] = evecs
                    freqs[q, :] = evals
                else:
                    split_i = np.concatenate((split_i, [q]))
                    split_freqs = np.concatenate((split_freqs, evals[np.newaxis]))
                    split_eigenvecs = np.concatenate((split_eigenvecs, evecs[np.newaxis]))

        freqs = (freqs*ureg.hartree).to(self.freqs.units, 'spectroscopy')
        split_freqs = (split_freqs*ureg.hartree).to(self.split_freqs.units, 'spectroscopy')
        if set_attrs:
            self.asr = asr
            self.dipole = dipole
            self.n_qpts = n_qpts
            self.qpts = qpts
            self.weights = np.full(len(qpts), 1.0/n_qpts)
            self.freqs = freqs
            self.eigenvecs = eigenvecs

            self.split_i = split_i
            self.split_freqs = split_freqs
            self.split_eigenvecs = split_eigenvecs

        return freqs, eigenvecs


    def _calculate_dyn_mat(self, q, fc_img_weighted, unique_sc_offsets,
                           unique_sc_i, unique_cell_origins, unique_cell_i):
        """
        Calculate the non mass weighted dynamical matrix at a specified
        q-point from the image weighted force constants matrix and the indices
        specifying the periodic images. See eq. 1.5:
        http://www.tcm.phy.cam.ac.uk/castep/Phonons_Guide/Castep_Phonons.html

        Parameters
        ----------
        q : ndarray
            The q-point to calculate the correction for
            dtype = 'float'
            shape = (3,)
        fc_img_weighted : ndarray
            The force constants matrix weighted by the number of supercell ion
            images for each ij displacement
            dtype = 'float'
            shape = (3*n_ions*n_cells_in_sc, 3*n_ions)
        unique_sc_offsets : list of lists of ints
            A list containing 3 lists of the unique supercell image offsets in
            each direction. The supercell offset is calculated by multiplying
            the supercell matrix by the supercell image indices (obtained by
            _get_all_origins()). A list of lists rather than a
            Numpy array is used as the 3 lists are independent and their size
            is not known beforehand
        unique_sc_i : ndarray
            The indices needed to reconstruct sc_offsets from the unique
            values in unique_sc_offsets
            dtype = 'int'
            shape = ((2*lim + 1)**3, 3)
        unique_cell_origins : list of lists of ints
            A list containing 3 lists of the unique cell origins in each
            direction. A list of lists rather than a Numpy array is used as
            the 3 lists are independent and their size is not known beforehand
        unique_sc_i : ndarray
            The indices needed to reconstruct cell_origins from the unique
            values in unique_cell_origins
            dtype = 'int'
            shape = (cell_origins, 3)

        Returns
        -------
        dyn_mat : ndarray
            The non mass weighted dynamical matrix at q
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)
        """

        n_ions = self.n_ions
        n_cells_in_sc = self.n_cells_in_sc
        sc_image_i = self.sc_image_i
        max_sc_images = self.max_sc_images
        dyn_mat = np.zeros((n_ions*3, n_ions*3), dtype=np.complex128)

        # Cumulant method: for each ij ion-ion displacement sum phases for
        # all possible supercell images, then multiply by the cell phases
        # to account for j ions in different cells. Then multiply by the
        # image weighted fc matrix for each 3 x 3 ij displacement

        # Make sc_phases 1 longer than necessary, so when summing phases for
        # supercell images if there is no image, an index of -1 and hence
        # phase of zero can be used
        sc_phases = np.zeros(len(unique_sc_i) + 1, dtype=np.complex128)
        sc_phases[:-1], cell_phases = self._calculate_phases(
            q, unique_sc_offsets, unique_sc_i, unique_cell_origins,
            unique_cell_i)
        sc_phase_sum = np.sum(sc_phases[sc_image_i[:,:,:,0:max_sc_images]],
                              axis=3)

        ax = np.newaxis
        ij_phases = cell_phases[:,ax,ax]*sc_phase_sum
        full_dyn_mat = fc_img_weighted*(
            np.transpose(ij_phases, axes=[0,2,1])
            .repeat(3, axis=2)
            .repeat(3, axis=1))
        dyn_mat = np.sum(full_dyn_mat, axis=0)

        # Need to transpose dyn_mat to have [i, j] ion indices, as it was
        # formed by summing the force_constants matrix which has [j, i]
        # indices
        return np.transpose(dyn_mat)


    def _dipole_correction_init(self):
        """
        Calculate the q-independent parts of the long range correction to the
        dynamical matrix for efficiency. The method used is based on the
        Ewald sum, see eqs 72-74 from Gonze and Lee PRB 55, 10355 (1997)
        """

        cell_vec = self.cell_vec.to('bohr').magnitude
        recip = reciprocal_lattice(cell_vec)
        n_ions = self.n_ions
        ion_r = self.ion_r
        born = self.born.magnitude
        dielectric = self.dielectric
        inv_dielectric = np.linalg.inv(dielectric)
        epsilon = 1e-10
        sqrt_pi = math.sqrt(math.pi)

        # Calculate cutoffs
        abc_mag = np.linalg.norm(cell_vec, axis=1)
        mean_abc_mag = np.prod(abc_mag)**(1.0/3)
        skew = np.amax(abc_mag)/mean_abc_mag
        eta = (sqrt_pi/mean_abc_mag)*n_ions**(1.0/6)
        precision = 50
        recip_scale = 1.0
        real_cutoff = math.sqrt(precision)*skew
        recip_cutoff = recip_scale*math.sqrt(precision)*skew

        # Calculate realspace cells
        abc = math.sqrt((real_cutoff/eta)**2 + np.sum(
            np.sum(np.abs(cell_vec), axis=0)**2))
        max_cells_abc = (abc/abc_mag).astype(np.int32) + 1
        n_cells_abc = 2*max_cells_abc + 1
        n_cells_tot = n_cells_abc.prod()
        cell_origins = self._get_all_origins(
            max_cells_abc + 1, min_xyz=-max_cells_abc)
        cell_origins_cart = np.einsum('ij,jk->ik', cell_origins, cell_vec)

        # Calculate reciprocal space vectors
        hkl_mag = np.linalg.norm(recip, axis=1)
        hkl = math.sqrt((recip_cutoff*2*eta)**2 + np.sum(
            np.sum(np.abs(recip), axis=0)**2))
        max_cells_hkl = (hkl/hkl_mag).astype(np.int32) + 1
        n_cells_hkl = 2*max_cells_hkl + 1
        n_cells_recip = n_cells_hkl.prod()
        gvecs = self._get_all_origins(
            max_cells_hkl + 1, min_xyz=-max_cells_hkl)
        gvecs_cart = np.einsum('ij,jk->ik', gvecs, recip)

        # Use eta = lambda * |permittivity|**(1/6)
        eta =  eta*np.power(np.linalg.det(dielectric), 1.0/6)
        eta_2 = eta**2

        # Calculate q=0 real space term
        real_q0 = np.zeros((n_ions, n_ions, 3, 3))
        H_ab = np.zeros((n_ions, n_ions, n_cells_tot, 3, 3))
        cells_in_range = np.zeros((n_ions, n_ions, n_cells_tot),
                                  dtype=np.int32)
        n_cells_in_range = np.zeros((n_ions, n_ions), dtype=np.int32)

        ion_r_cart = np.einsum('ij,jk->ik', ion_r, cell_vec)
        ion_r_e = np.einsum('ij,jk->ik', ion_r_cart, inv_dielectric)
        cell_origins_e = np.einsum(
            'ij,jk->ik', cell_origins_cart, inv_dielectric)
        for i in range(n_ions):
            for j in range(n_ions):
                rij_cart = ion_r_cart[i] - ion_r_cart[j]
                rij_e = ion_r_e[i] - ion_r_e[j]
                diffs = rij_cart - cell_origins_cart
                deltas = rij_e - cell_origins_e
                norms_2 = np.einsum('ij,ij->i', deltas, diffs)*eta_2
                norms = np.sqrt(norms_2)
                idx = np.where(np.logical_and(norms > epsilon,
                                              norms < real_cutoff))[0]
                n_cells_in_range[i,j] = len(idx)
                cells_in_range[i,j,:len(idx)] = idx

                # Reindex some already calculated values to only include
                # cells in range
                deltas = deltas[idx]
                norms_2 = norms_2[idx]
                norms = norms[idx]

                # Calculate H_ab
                exp_term = 2*np.exp(-norms_2)/(sqrt_pi*norms_2)
                erfc_term = erfc(norms)/(norms*norms_2)
                f1 = eta_2*(3*erfc_term/norms_2 + exp_term*(3/norms_2 + 2))
                f2 = erfc_term + exp_term
                deltas_ab = np.einsum('ij,ik->ijk', deltas, deltas)
                H_ab[i,j,:len(idx)] = (np.einsum('i,ijk->ijk', f1, deltas_ab)
                                       - np.einsum('i,jk->ijk',
                                                   f2, inv_dielectric))
        real_q0 = np.sum(H_ab, axis=2)
        real_q0 *= eta**3/math.sqrt(np.linalg.det(dielectric))


        # Calculate the q=0 reciprocal term
        recip_q0 = np.zeros((n_ions, n_ions, 3, 3), dtype=np.complex128)
        # Calculate g-vector phases
        gvec_dot_r = np.einsum('ij,kj->ik', gvecs, ion_r)
        gvec_phases = np.exp(2j*math.pi*gvec_dot_r)
        self.gvec_phases = gvec_phases # Assign before reindexing
        # Calculate g-vector symmetric matrix
        gvecs_ab = np.einsum('ij,ik->ijk', gvecs_cart, gvecs_cart)
        # Calculate which reciprocal vectors are within the cutoff
        k_len_2 = np.einsum('ijk,jk->i', gvecs_ab, dielectric)/(4*eta_2)
        k_len = np.sqrt(k_len_2)
        idx = np.where(np.logical_and(k_len > epsilon,
                                      k_len < recip_cutoff))[0]
        # Reindex to only include vectors within cutoff
        k_len_2 = k_len_2[idx]
        k_len = k_len[idx]
        gvecs_ab = gvecs_ab[idx]
        gvec_phases = gvec_phases[idx]
        recip_exp = np.exp(-k_len_2)/k_len_2
        for i in range(n_ions):
            for j in range(n_ions):
                phase_exp = gvec_phases[:,i]/gvec_phases[:,j]
                recip_q0[i,j] = np.einsum(
                    'ijk,i,i->jk', gvecs_ab, phase_exp, recip_exp)
        cell_volume = np.dot(cell_vec[0], np.cross(cell_vec[1], cell_vec[2]))
        recip_q0 *= math.pi/(cell_volume*eta_2)

        # Calculate the q=0 correction, to be subtracted from the corrected
        # diagonal at each q
        dipole_q0 = np.zeros((n_ions, 3, 3), dtype=np.complex128)
        for i in range(n_ions):
            for j in range(n_ions):
                for a in range(3):
                    for b in range(3):
                        dipole_q0[i, a,b] += np.sum(
                            np.einsum('i,j', born[i,a,:], born[j,b,:])
                            *(recip_q0[i,j] - real_q0[i,j]))
            # Symmetrise
            dipole_q0[i] = 0.5*(dipole_q0[i] + np.transpose(dipole_q0[i]))

        self.max_cells_abc = max_cells_abc
        self.max_cells_hkl = max_cells_hkl
        self.gvecs_cart = gvecs_cart
        self.recip_cutoff = recip_cutoff
        self.eta = eta

        # Don't keep any entries beyond the cutoff
        max_n_cells_in_range = np.amax(n_cells_in_range)
        self.n_cells_in_range = n_cells_in_range
        self.cells_in_range = cells_in_range[:, :, :max_n_cells_in_range]
        self.H_ab = H_ab[:, :, :max_n_cells_in_range, :, :]
        self.dipole_q0 = dipole_q0


    def _calculate_dipole_correction(self, q):
        """
        Calculate the long range correction to the dynamical matrix using the
        Ewald sum, see eqs 72-74 from Gonze and Lee PRB 55, 10355 (1997)

        Parameters
        ----------
        q : ndarray
            The q-point to calculate the correction for
            dtype = 'float'
            shape = (3,)

        Returns
        -------
        corr : ndarray
            The correction to the dynamical matrix
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)
        """
        cell_vec = self.cell_vec.to('bohr').magnitude
        recip = reciprocal_lattice(cell_vec)
        n_ions = self.n_ions
        ion_r = self.ion_r
        born = self.born.magnitude
        dielectric = self.dielectric
        inv_dielectric = np.linalg.inv(dielectric)
        eta = self.eta
        eta_2 = eta**2
        max_cells_abc = self.max_cells_abc
        max_cells_hkl = self.max_cells_hkl
        recip_cutoff = self.recip_cutoff
        H_ab = self.H_ab
        cells_in_range = self.cells_in_range
        gvec_phases = self.gvec_phases
        gvecs_cart = self.gvecs_cart

        q_norm = q - np.rint(q) # Normalised q-pt
        epsilon = 1e-10

        # Calculate realspace cells
        n_cells_abc = 2*max_cells_abc + 1
        n_cells_tot = n_cells_abc.prod()
        cell_origins = self._get_all_origins(
            max_cells_abc + 1, min_xyz=-max_cells_abc)


        # Calculate real space term
        real_dipole = np.zeros((n_ions, n_ions, 3, 3), dtype=np.complex128)
        # Calculate real space phase factor
        q_dot_ra = np.einsum('i,ji->j', q_norm, cell_origins)
        real_phases = np.exp(2j*math.pi*q_dot_ra)
        for i in range(n_ions):
            for j in range(i, n_ions):
                real_dipole[i,j] = np.einsum(
                    'ijk,i->jk', H_ab[i,j], real_phases[cells_in_range[i,j]])
        real_dipole *= eta**3/math.sqrt(np.linalg.det(dielectric))


        # Calculate reciprocal term
        recip_dipole = np.zeros((n_ions, n_ions, 3, 3), dtype=np.complex128)
        # Calculate q-point phases
        q_dot_r = np.einsum('i,ji->j', q_norm, ion_r)
        q_phases = np.exp(2j*math.pi*q_dot_r)
        q_cart = np.dot(q_norm, recip)
        # Calculate k-vector symmetric matrix
        kvecs = gvecs_cart + q_cart
        kvecs_ab = np.einsum('ij,ik->ijk', kvecs, kvecs)
        # Calculate which reciprocal vectors are within the cutoff
        k_len_2 = np.einsum('ijk,jk->i', kvecs_ab, dielectric)/(4*eta_2)
        k_len = np.sqrt(k_len_2)
        idx = np.where(np.logical_and(k_len > epsilon,
                                      k_len < recip_cutoff))[0]
        # Reindex to only include vectors within cutoff
        k_len_2 = k_len_2[idx]
        k_len = k_len[idx]
        kvecs_ab = kvecs_ab[idx]
        gvec_phases = gvec_phases[idx]
        recip_exp = np.einsum('ijk,i->ijk', kvecs_ab, np.exp(-k_len_2)/k_len_2)
        for i in range(n_ions):
            for j in range(i, n_ions):
                phase_exp = ((gvec_phases[:,i]*q_phases[i])
                             /(gvec_phases[:,j]*q_phases[j]))
                recip_dipole[i,j] = np.einsum(
                    'ijk,i->jk', recip_exp, phase_exp)
        cell_volume = np.dot(cell_vec[0], np.cross(cell_vec[1], cell_vec[2]))
        recip_dipole *= math.pi/(cell_volume*eta_2)

        # Fill in remaining entries by symmetry
        for i in range(1, n_ions):
            for j in range(i):
                real_dipole[i,j] = np.conj(real_dipole[j,i])
                recip_dipole[i,j] = np.conj(recip_dipole[j,i])

        dipole = np.zeros((n_ions, n_ions, 3, 3), dtype=np.complex128)
        dipole_tmp = recip_dipole - real_dipole
        for i in range(n_ions):
            for j in range(n_ions):
                for a in range(3):
                    dipole[i,j,a,:] = np.einsum('i,jk,ik->j', born[i,a,:],
                                                born[j,:,:], dipole_tmp[i,j])

            dipole[i,i] -= self.dipole_q0[i]

        return np.reshape(
            np.transpose(dipole, axes=[0, 2, 1, 3]), (3*n_ions, 3*n_ions))


    def _calculate_gamma_correction(self, q_dir):
        """
        Calculate non-analytic correction to the dynamical matrix at q=0 for
        a specified direction of approach. See Eq. 60 of X. Gonze and C. Lee,
        PRB (1997) 55, 10355-10368.

        Parameters
        ----------
        q_dir : ndarray
            The direction along which q approaches 0, in reciprocal fractional
            coordinates
            dtype = 'float'
            shape = (3,)

        Returns
        -------
        na_corr : ndarray
            The correction to the dynamical matrix
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)
        """
        cell_vec = self.cell_vec.to('bohr').magnitude
        n_ions = self.n_ions
        born = self.born.magnitude
        dielectric = self.dielectric

        cell_volume = np.dot(cell_vec[0], np.cross(cell_vec[1], cell_vec[2]))
        denominator = np.einsum('ij,i,j', dielectric, q_dir, q_dir)
        factor = 4*math.pi/(cell_volume*denominator)

        q_born_sum = np.einsum('ijk,k->ij', born, q_dir)
        na_corr = np.zeros((3*n_ions, 3*n_ions), dtype=np.complex128)
        for i in range(n_ions):
            for j in range(n_ions):
                na_corr[3*i:3*(i+1), 3*j:3*(j+1)] = np.einsum(
                    'i,j->ij', q_born_sum[i], q_born_sum[j])
        na_corr *= factor

        return na_corr


    def _get_all_origins(self, max_xyz, min_xyz=[0, 0, 0], step=1):
        """
        Given the max/min number of cells in each direction, get a list of all
        possible cell origins

        Parameters
        ----------
        max_xyz : ndarray
            The number of cells to count to in each direction
            dtype = 'int'
            shape = (3,)
        min_xyz : ndarray, optional, default [0,0,0]
            The cell number to count from in each direction
            dtype = 'int'
            shape = (3,)
        step : integer, optional, default 1
            The step between cells

        Returns
        -------
        origins : ndarray
            The cell origins
            dtype = 'int'
            shape = (prod(max_xyz - min_xyz)/step, 3)
        """
        diff = np.absolute(max_xyz - min_xyz)
        nx = np.repeat(range(min_xyz[0], max_xyz[0], step), diff[1]*diff[2])
        ny = np.repeat(np.tile(range(min_xyz[1], max_xyz[1], step), diff[0]),
                       diff[2])
        nz = np.tile(range(min_xyz[2], max_xyz[2], step), diff[0]*diff[1])

        return np.column_stack((nx, ny, nz))


    def _enforce_realspace_asr(self):
        """
        Apply a transformation to the force constants matrix so that it
        satisfies the acousic sum rule. Diagonalise, shift the acoustic modes
        to almost zero then construct the correction to the force constants
        matrix using the eigenvectors. For more information see section 2.3.4:
        http://www.tcm.phy.cam.ac.uk/castep/Phonons_Guide/Castep_Phonons.html

        Returns
        -------
        force_constants : ndarray
            The corrected force constants matrix
            dtype = 'float'
            shape = (n_cells_in_sc, 3*n_ions, 3*n_ions)
        """
        cell_vec = self.cell_vec
        cell_origins = self.cell_origins
        sc_matrix = self.sc_matrix
        n_cells_in_sc = self.n_cells_in_sc
        n_ions = self.n_ions
        n_branches = self.n_branches
        force_constants = self.force_constants.magnitude
        ax = np.newaxis

        # Compute square matrix giving relative index of cells in sc
        n_ions_in_sc = n_ions*n_cells_in_sc
        sq_fc = np.zeros((3*n_ions_in_sc, 3*n_ions_in_sc))
        inv_sc_matrix = np.linalg.inv(np.transpose(sc_matrix))
        cell_origins_sc = np.einsum('ij,kj->ik', cell_origins, inv_sc_matrix)
        for nc in range(n_cells_in_sc):
            # Get all possible cell-cell vector combinations
            inter_cell_vectors = cell_origins_sc - np.tile(cell_origins_sc[nc],
                                                           (n_cells_in_sc, 1))
            # Compare cell-cell vectors with origin-cell vectors and determine
            # which are equivalent
            # Do calculation in chunks, so loop can be broken if all
            # equivalent vectors have been found
            N = 100
            dist_min = np.full((n_cells_in_sc), sys.float_info.max)
            sc_relative_index = np.zeros(n_cells_in_sc, dtype=np.int32)
            for i in range(int((n_cells_in_sc - 1)/N) + 1):
                ci = i*N
                cf = min((i + 1)*N, n_cells_in_sc)
                dist = (inter_cell_vectors[:, ax, :] -
                        cell_origins_sc[ax, ci:cf, :])
                dist_frac = dist - np.rint(dist)
                dist_frac_sum = np.sum(np.abs(dist_frac), axis=2)
                scri_current = np.argmin(dist_frac_sum, axis=1)
                dist_min_current = dist_frac_sum[
                    range(n_cells_in_sc), scri_current]
                replace =  dist_min_current < dist_min
                sc_relative_index[replace] = ci + scri_current[replace]
                dist_min[replace] = dist_min_current[replace]
                if np.all(dist_min <= 16*sys.float_info.epsilon):
                    break
            if (np.any(dist_min > 16*sys.float_info.epsilon)):
                warnings.warn(('Error correcting FC matrix for acoustic sum '
                               'rule, supercell relative index couldn\'t be '
                               'found. Returning uncorrected FC matrix'))
                return self.force_constants
            sq_fc[3*nc*n_ions:3*(nc+1)*n_ions, :] = np.transpose(
                np.reshape(force_constants[sc_relative_index],
                           (3*n_cells_in_sc*n_ions, 3*n_ions)))
        try:
            ac_i, evals, evecs = self._find_acoustic_modes(sq_fc)
        except:
            warnings.warn(('\nError correcting for acoustic sum rule, could '
                           'not find 3 acoustic modes.\nReturning uncorrected '
                           'FC matrix'), stacklevel=2)
            return self.force_constants

        # Correct force constant matrix - set acoustic modes to almost zero
        fc_tol = 1e-8*np.min(np.abs(evals))
        for ac in ac_i:
            sq_fc -= (fc_tol + evals[ac])*np.einsum(
                'i,j->ij', evecs[:, ac], evecs[:, ac])

        fc = np.reshape(sq_fc[:, :3*n_ions],
                        (n_cells_in_sc, 3*n_ions, 3*n_ions))
        fc = fc*self.force_constants.units

        return fc


    def _enforce_reciprocal_asr(self, dyn_mat_gamma, dyn_mat):
        """
        Apply a transformation to the dynamical matrix at so that it
        satisfies the acousic sum rule. Diagonalise, shift the acoustic modes
        to almost zero then reconstruct the dynamical matrix using the
        eigenvectors. For more information see section 2.3.4:
        http://www.tcm.phy.cam.ac.uk/castep/Phonons_Guide/Castep_Phonons.html

        Parameters
        ----------
        dyn_mat_gamma : ndarray
            The non mass-weighted dynamical matrix at q=0
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)
        dyn_mat : ndarray
            The uncorrected, non mass-weighted dynamical matrix at q
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)

        Returns
        -------
        dyn_mat : ndarray
            The corrected, non mass-weighted dynamical matrix at q
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)
        """
        try:
            ac_i, evals, evecs = self._find_acoustic_modes(dyn_mat_gamma)
        except:
            warnings.warn(('\nError correcting for acoustic sum rule, could '
                           'not find 3 acoustic modes.\nReturning uncorrected '
                           'dynamical matrix'), stacklevel=2)
            return dyn_mat
        tol = 1e-8*np.min(np.abs(evals))

        for i, ac in enumerate(ac_i):
            dyn_mat -= (tol*i + evals[ac])*np.einsum(
                'i,j->ij', evecs[:, ac], evecs[:, ac])

        return dyn_mat


    def _find_acoustic_modes(self, dyn_mat):
        """
        Find the acoustic modes from a dynamical matrix, they should have
        the sum of c of m amplitude squared = mass (note: have not actually
        included mass weighting here so assume mass = 1.0)

        Parameters
        ----------
        dyn_mat : ndarray
            A dynamical matrix
            dtype = 'complex'
            shape = (3*n_ions, 3*n_ions)

        Returns
        -------
        ac_i : ndarray
            The indices of the acoustic modes
            dtype = 'int'
            shape = (3,)
        evals : ndarray
            Dynamical matrix eigenvalues
            dtype = 'float'
            shape = (3*n_ions)
        evecs : ndarray
            Dynamical matrix eigenvectors
            dtype = 'complex'
            shape = (3*n_ions, n_ions, 3)
        """
        n_branches = dyn_mat.shape[0]
        n_ions = int(n_branches/3)

        evals, evecs = np.linalg.eigh(dyn_mat)
        evec_reshape = np.reshape(
            np.transpose(evecs), (n_branches, n_ions, 3))
        # Sum displacements for all ions in each branch
        c_of_m_disp = np.sum(evec_reshape, axis=1)
        c_of_m_disp_sq = np.sum(np.abs(c_of_m_disp)**2, axis=1)
        sensitivity = 0.5
        sc_mass = 1.0*n_ions
        # Check number of acoustic modes
        if np.sum(c_of_m_disp_sq > sensitivity*sc_mass) < 3:
            raise Exception('Could not find 3 acoustic modes')
        # Find indices of acoustic modes (3 largest c of m displacements)
        ac_i = np.argsort(c_of_m_disp_sq)[-3:]

        return ac_i, evals, evecs


    def _calculate_phases(self, q, unique_sc_offsets, unique_sc_i, unique_cell_origins, unique_cell_i):
        """
        Calculate the phase factors for the supercell images and cells for a
        single q-point. The unique supercell and cell origins indices are
        required to minimise expensive exp and power operations

        Parameters
        ----------
        q : ndarray
            The q-point to calculate the phase for
            dtype = 'float'
            shape = (3,)
        unique_sc_offsets : list of lists of ints
            A list containing 3 lists of the unique supercell image offsets in
            each direction. The supercell offset is calculated by multiplying
            the supercell matrix by the supercell image indices (obtained by
            _get_all_origins()). A list of lists rather than a
            Numpy array is used as the 3 lists are independent and their size
            is not known beforehand
        unique_sc_i : ndarray
            The indices needed to reconstruct sc_offsets from the unique
            values in unique_sc_offsets
            dtype = 'int'
            shape = ((2*lim + 1)**3, 3)
        unique_cell_origins : list of lists of ints
            A list containing 3 lists of the unique cell origins in each
            direction. A list of lists rather than a Numpy array is used as
            the 3 lists are independent and their size is not known beforehand
        unique_cell_i : ndarray
            The indices needed to reconstruct cell_origins from the unique
            values in unique_cell_origins
            dtype = 'int'
            shape = (cell_origins, 3)

        Returns
        -------
        sc_phases : ndarray
            Phase factors exp(iq.r) for each supercell image coordinate in
            sc_offsets
            dtype = 'float'
            shape = (unique_sc_i,)
        cell_phases : ndarray
            Phase factors exp(iq.r) for each cell coordinate in the supercell
            dtype = 'float'
            shape = (unique_cell_i,)
        """

        # Only calculate exp(iq) once, then raise to power to get the phase at
        # different supercell/cell coordinates to minimise expensive exp
        # calculations
        # exp(iq.r) = exp(iqh.ra)*exp(iqk.rb)*exp(iql.rc)
        #           = (exp(iqh)^ra)*(exp(iqk)^rb)*(exp(iql)^rc)
        phase = np.exp(2j*math.pi*q)
        sc_phases = np.ones(len(unique_sc_i), dtype=np.complex128)
        cell_phases = np.ones(len(unique_cell_i), dtype=np.complex128)
        for i in range(3):
            unique_sc_phases = np.power(phase[i], unique_sc_offsets[i])
            sc_phases *= unique_sc_phases[unique_sc_i[:, i]]

            unique_cell_phases = np.power(phase[i], unique_cell_origins[i])
            cell_phases *= unique_cell_phases[unique_cell_i[:, i]]

        return sc_phases, cell_phases


    def _calculate_supercell_images(self, lim):
        """
        For each displacement of ion i in the unit cell and ion j in the
        supercell, calculate the number of supercell periodic images there are
        and which supercells they reside in, and sets the sc_image_i,
        n_sc_images and max_sc_images InterpolationData attributes

        Parameters
        ----------
        lim : int
            The supercell image limit
        """

        n_ions = self.n_ions
        cell_vec = self.cell_vec.to(ureg.bohr).magnitude
        ion_r = self.ion_r
        cell_origins = self.cell_origins
        n_cells_in_sc = self.n_cells_in_sc
        sc_matrix = self.sc_matrix

        # List of points defining Wigner-Seitz cell
        ws_frac = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1],
                            [0, 1, -1], [1, 0, 0], [1, 0, 1], [1, 0, -1],
                            [1, 1, 0], [1, 1, 1], [1, 1, -1], [1, -1, 0],
                            [1, -1, 1], [1, -1, -1]])
        cutoff_scale = 1.0

        # Calculate points of WS cell for this supercell
        sc_vecs = np.dot(sc_matrix, cell_vec)
        ws_list = np.dot(ws_frac, sc_vecs)
        inv_ws_sq = 1.0/np.sum(np.square(ws_list[1:]), axis=1)

        # Get Cartesian coords of supercell images and ions in supercell
        sc_image_r = self._get_all_origins(
            np.repeat(lim, 3) + 1, min_xyz=-np.repeat(lim, 3))
        sc_image_cart = np.einsum('ij,jk->ik', sc_image_r, sc_vecs)
        ax = np.newaxis
        sc_ion_r = np.einsum('ijk,kl->ijl',
                             cell_origins[:,ax,:] + ion_r[ax,:,:],
                             np.linalg.inv(np.transpose(sc_matrix)))
        sc_ion_cart = np.einsum('ijk,kl->ijl', sc_ion_r, sc_vecs)

        sc_image_i = np.full((n_cells_in_sc, n_ions, n_ions, (2*lim + 1)**3),
                             -1, dtype=np.int8)
        n_sc_images = np.zeros((n_cells_in_sc, n_ions, n_ions), dtype=np.int8)
        for nc in range(n_cells_in_sc):
            for i in range(n_ions):
                for j in range(n_ions):
                    # Get vector between j in supercell image and i
                    dists = sc_ion_cart[0,i] - sc_ion_cart[nc,j] - sc_image_cart
                    # Compare ion-ion supercell vector and all ws point vectors
                    dist_ws_points = np.einsum('ij,kj->ik', dists, ws_list[1:])
                    dist_wsp_frac = np.absolute(
                        np.einsum('ij,j->ij', dist_ws_points, inv_ws_sq))
                    # Count images if ion < half distance to all ws points
                    sc_images = np.where((np.amax(dist_wsp_frac, axis=1)
                                          <= (0.5*cutoff_scale + 0.001)))[0]
                    sc_image_i[nc,i,j,0:len(sc_images)] = sc_images
                    n_sc_images[nc,i,j] = len(sc_images)

        self.sc_image_i = sc_image_i
        self.n_sc_images = n_sc_images
        self.max_sc_images = np.max(self.n_sc_images)


    def convert_e_units(self, units):
        """
        Convert energy units of relevant attributes in place e.g. freqs,
        dos_bins

        Parameters
        ----------
        units : str
            The units to convert to e.g. '1/cm', 'hartree', 'eV'
        """
        super(InterpolationData, self).convert_e_units(units)

        if hasattr(self, 'freqs'):
            self.freqs.ito(units, 'spectroscopy')
            self.split_freqs.ito(units, 'spectroscopy')