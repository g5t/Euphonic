.. _calc_ins:

====================================================
Calculating Inelastic Neutron Scattering Intensities
====================================================

Theory
------

The one-phonon inelastic neutron scattering intensity can be calculated as:

.. math::

   S(Q, \omega) = |F(Q, \nu)|^2
   (n_\nu+\frac{1}{2}\pm\frac{1}{2})
   \delta(\omega\mp\omega_{q\nu})

   F(Q, \nu) = \frac{b_\kappa}{M_{\kappa}^{1/2}\omega_{q\nu}^{1/2}}
   [Q\cdot\epsilon_{q\nu\kappa\alpha}]e^{Q{\cdot}r_\kappa}e^{-W}

:math:`n_\nu` is the Bose-Einstein distribution:

.. math::

   n_\nu = \frac{1}{e^{\frac{\hbar\omega_\nu}{k_{B}T}} - 1}

:math:`e^{-W}` is the Debye-Waller factor:

.. math::

   e^{-\sum_{\alpha\beta}\frac{W^{\kappa}_{\alpha\beta}Q_{\alpha}Q_{\beta}}{2}}

.. math::

   W^{\kappa}_{\alpha\beta} =
   \frac{1}{2N_{q}M_{\kappa}}
   \sum_{BZ}\frac{\epsilon_{q\nu\kappa\alpha}\epsilon^{*}_{q\nu\kappa\beta}}
   {\omega_{q\nu}}
   coth(\frac{\omega_{q\nu}}{2k_BT})

Where :math:`\nu` runs over phonon modes, :math:`\kappa` runs over atoms, 
:math:`\alpha,\beta` run over the Cartesian directions, :math:`b_\kappa` is the
coherent neutron scattering length, :math:`M_{\kappa}` is the atom mass,
:math:`r_{\kappa}` is the vector to atom :math:`\kappa` in the unit cell, 
:math:`\epsilon_{q\nu\kappa\alpha}` are the eigevectors, :math:`\omega_{q\nu}`
are the frequencies, :math:`\sum_{BZ}` is a sum over the 1st Brillouin Zone, and
:math:`N_q` is the number of q-point samples in the BZ.

Usage
-----

The neutron structure factor can be calculated for each branch and q-point for
both ``PhononData`` objects and ``InterpolationData`` objects for which
frequencies/eigenvectors have already been calculated, using the
``calculate_structure_factor`` method. A dictionary of coherent neutron
scattering lengths in fm must also be provided.

Calculation of the Debye-Waller factor is optional, to calculate it a
``PhononData/InterpolationData`` object with the phonons calculated on a q-point
grid must be provided as the ``dw_data`` keyword argument to
``calculate_structure_factor``. See below example:

.. code-block:: py

    import seekpath
    import numpy as np
    from euphonic.data.interpolation import InterpolationData
    from euphonic.util import mp_grid

    # Read quartz data from quartz.castep_bin
    idata = InterpolationData.from_castep('quartz')

    # Generate a recommended q-point path using seekpath
    _, unique_ions = np.unique(idata.ion_type, return_inverse=True)
    structure = (idata.cell_vec.magnitude, idata.ion_r, unique_ions)
    qpts = seekpath.get_explicit_k_path(structure)["explicit_kpoints_rel"]

    # Calculate frequencies/eigenvectors for the q-point path
    idata.calculate_fine_phonons(qpts, asr='reciprocal')

    # For the DW calculation, generate and calculate frequencies/eigenvectors on
    # a grid (generate a Monkhorst-Pack grid of q-points using the mp-grid
    # helper function)
    q_grid = mp_grid([5,5,5])
    dw_idata = InterpolationData.from_castep('quartz')
    dw_idata.calculate_fine_phonons(q_grid, asr='reciprocal')

    # Calculate structure factor for each q-point in idata. Structure factor is
    # returned, but not stored in the Data object
    scattering_lengths = {'Si': 4.1491, 'O': 5.803}
    sf = idata.calculate_structure_factor(scattering_lengths, T=5,
                                          dw_data=dw_idata)

Optional Keyword Arguments
--------------------------

**T**

This is the temperature in Kelvin, and affects the Bose-Einstein distribution
and the Debye-Waller factor. By default ``T=5``, but set ``T=0`` to ignore
temperature effects.

**scale**

Apply a multiplicative factor to the final structure factor. By default
``scale=1.0``

**calc_bose**

Whether to calculate and multiply by the value of the Bose distribution at each
frequency. By default ``calc_bose=True``

**dw_data**

This is a ``PhononData`` or ``InterpolationData`` object with
frequencies/eigenvectors calculated on a grid of q-points. The grid density
required to get a good convergence of the Debye-Waller factor depends on the
material and some trial and error may be required to get good convergence

Docstring
---------
.. autofunction:: euphonic.data.interpolation.InterpolationData.calculate_structure_factor