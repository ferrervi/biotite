# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

"""
This module provides functions for basepair identification.
"""

__name__ = "biotite.structure"
__author__ = "Tom David Müller"
__all__ = ["base_pairs", "map_nucleotide", "base_stacking"]

import numpy as np
import warnings
from .atoms import Atom, array
from .superimpose import superimpose, superimpose_apply
from .filter import filter_nucleotides
from .celllist import CellList
from .hbond import hbond
from .error import IncompleteStructureWarning, UnexpectedStructureWarning
from .util import distance, norm_vector
from .residues import get_residue_starts_for, get_residue_masks
from .info.standardize import standardize_order
from .compare import rmsd


def _get_std_adenine():
    """
    Get standard base variables for adenine.

    Returns
    -------
    standard_base : AtomArray
        Standard coordinates nomenclature of the adenine base as
        :class:`AtomArray` with nomenclature of PDB File Format V3
    coordinates : tuple (ndarray, ndarray, ndarray, dtype=float)
        :class:`ndarray` containing the center according to the SCHNaP-
        paper referenced in the function ``base_pairs``,
        :class:`ndarray` containing the coordinates of the pyrimidine
        ring center, :class:`ndarray` containing the coordinates of the
        imidazole ring center
    """
    atom1 =  Atom([-1.291, 4.498, 0.000], atom_name="N9",  res_name="A")
    atom2 =  Atom([0.024, 4.897, 0.000],  atom_name="C8",  res_name="A")
    atom3 =  Atom([0.877, 3.902, 0.000],  atom_name="N7",  res_name="A")
    atom4 =  Atom([0.071, 2.771, 0.000],  atom_name="C5",  res_name="A")
    atom5 =  Atom([0.369, 1.398, 0.000],  atom_name="C6",  res_name="A")
    atom6 =  Atom([1.611, 0.909, 0.000],  atom_name="N6",  res_name="A")
    atom7 =  Atom([-0.668, 0.532, 0.000], atom_name="N1",  res_name="A")
    atom8 =  Atom([-1.912, 1.023, 0.000], atom_name="C2",  res_name="A")
    atom9 = Atom([-2.320, 2.290, 0.000], atom_name="N3",  res_name="A")
    atom10 = Atom([-1.267, 3.124, 0.000], atom_name="C4",  res_name="A")
    adenine = array(
        [atom1, atom2, atom3, atom4, atom5, atom6, atom7, atom8,
         atom9, atom10]
    )

    # Get the midpoint between the N1 and C4 atoms
    midpoint = np.mean([atom7.coord, atom10.coord], axis=-2)
    # Calculate the coordinates of the aromatic ring centers
    pyrimidine_center = np.mean(
        [atom4.coord, atom5.coord, atom7.coord,
         atom8.coord, atom9.coord, atom10.coord], axis=-2
    )
    imidazole_center = np.mean(
        [atom1.coord, atom2.coord, atom3.coord,
         atom4.coord, atom10.coord], axis=-2
    )

    return adenine, (midpoint, pyrimidine_center, imidazole_center)


def _get_std_cytosine():
    """
    Get standard base variables for cytosine.

    Returns
    -------
   standard_base : AtomArray
        Standard coordinates nomenclature of the cytosine base as
        :class:`AtomArray` with nomenclature of PDB File Format V3
    coordinates : tuple (ndarray, ndarray, dtype=float)
        :class:`ndarray` containing the center according to the SCHNaP-
        paper referenced in the function ``base_pairs``,
        :class:`ndarray` containing the coordinates of the pyrimidine
        ring center
    """
    atom1 = Atom([-1.285, 4.542, 0.000], atom_name="N1",  res_name="C")
    atom2 = Atom([-1.472, 3.158, 0.000], atom_name="C2",  res_name="C")
    atom3 = Atom([-2.628, 2.709, 0.000], atom_name="O2",  res_name="C")
    atom4 = Atom([-0.391, 2.344, 0.000], atom_name="N3",  res_name="C")
    atom5 = Atom([0.837, 2.868, 0.000],  atom_name="C4",  res_name="C")
    atom6 = Atom([1.875, 2.027, 0.000],  atom_name="N4",  res_name="C")
    atom7 = Atom([1.056, 4.275, 0.000],  atom_name="C5",  res_name="C")
    atom8 = Atom([-0.023, 5.068, 0.000], atom_name="C6",  res_name="C")
    cytosine = array(
        [atom1, atom2, atom3, atom4, atom5, atom6, atom7, atom8]
    )

    # Get the midpoint between the N3 and C6 atoms
    midpoint = np.mean([atom4.coord, atom8.coord], axis=-2)
    # Calculate the coordinates of the aromatic ring center
    pyrimidine_center = np.mean(
        [atom1.coord, atom2.coord, atom4.coord,
         atom5.coord, atom7.coord, atom8.coord], axis=-2
    )

    return cytosine, (midpoint, pyrimidine_center)


def _get_std_guanine():
    """
    Get standard base variables for guanine.

    Returns
    -------
    standard_base : AtomArray
        Standard coordinates nomenclature of the guanine base as
        :class:`AtomArray` with nomenclature of PDB File Format V3
    coordinates : tuple (ndarray, ndarray, ndarray, dtype=float)
        :class:`ndarray` containing the center according to the SCHNaP-
        paper referenced in the function ''base_pairs'',
        :class:`ndarray` containing the coordinates of the pyrimidine
        ring center, :class:`ndarray` containing the coordinates of the
        imidazole ring center
    """
    atom1 =  Atom([-1.289, 4.551, 0.000],  atom_name="N9",  res_name="G")
    atom2 =  Atom([0.023, 4.962, 0.000],   atom_name="C8",  res_name="G")
    atom3 =  Atom([0.870, 3.969, 0.000],   atom_name="N7",  res_name="G")
    atom4 =  Atom([0.071, 2.833, 0.000],   atom_name="C5",  res_name="G")
    atom5 =  Atom([0.424, 1.460, 0.000],   atom_name="C6",  res_name="G")
    atom6 =  Atom([1.554, 0.955, 0.000],   atom_name="O6",  res_name="G")
    atom7 =  Atom([-0.700, 0.641, 0.000],  atom_name="N1",  res_name="G")
    atom8 =  Atom([-1.999, 1.087, 0.000],  atom_name="C2",  res_name="G")
    atom9 = Atom([-2.949, 0.139, -0.001], atom_name="N2",  res_name="G")
    atom10 = Atom([-2.342, 2.364, 0.001],  atom_name="N3",  res_name="G")
    atom11 = Atom([-1.265, 3.177, 0.000],  atom_name="C4",  res_name="G")
    guanine = array(
        [atom1, atom2, atom3, atom4, atom5, atom6, atom7, atom8,
         atom9, atom10, atom11]
    )

    # Get the midpoint between the N1 and C4 atoms
    midpoint = np.mean([atom7.coord, atom11.coord], axis=-2)
    # Calculate the coordinates of the aromatic ring centers
    pyrimidine_center = np.mean(
        [atom4.coord, atom5.coord, atom7.coord,
         atom8.coord, atom10.coord, atom11.coord], axis=-2
    )
    imidazole_center = np.mean(
        [atom1.coord, atom2.coord, atom3.coord,
         atom4.coord, atom11.coord], axis=-2
    )

    return guanine, (midpoint, pyrimidine_center, imidazole_center)


def _get_std_thymine():
    """
    Get standard base variables for thymine.

    Returns
    -------
    standard_base : AtomArray
        Standard coordinates nomenclature of the thymine base as
        :class:`AtomArray` with nomenclature of PDB File Format V3
    coordinates : tuple (ndarray, ndarray, dtype=float)
        :class:`ndarray` containing the center according to the SCHNaP-
        paper referenced in the function ``base_pairs``,
        :class:`ndarray` containing the coordinates of the pyrimidine
        ring center
    """
    atom1 =  Atom([-1.284, 4.500, 0.000], atom_name="N1",  res_name="T")
    atom2 =  Atom([-1.462, 3.135, 0.000], atom_name="C2",  res_name="T")
    atom3 =  Atom([-2.562, 2.608, 0.000], atom_name="O2",  res_name="T")
    atom4 =  Atom([-0.298, 2.407, 0.000], atom_name="N3",  res_name="T")
    atom5 =  Atom([0.994, 2.897, 0.000],  atom_name="C4",  res_name="T")
    atom6 =  Atom([1.944, 2.119, 0.000],  atom_name="O4",  res_name="T")
    atom7 =  Atom([1.106, 4.338, 0.000],  atom_name="C5",  res_name="T")
    atom8 =  Atom([2.466, 4.961, 0.001],  atom_name="C7", res_name="T")
    atom9 = Atom([-0.024, 5.057, 0.000], atom_name="C6",  res_name="T")
    thymine = array(
        [atom1, atom2, atom3, atom4, atom5, atom6, atom7, atom8, atom9]
    )

    # Get the midpoint between the N3 and C6 atoms
    midpoint = np.mean([atom4.coord, atom9.coord], axis=-2)
    # Calculate the coordinates of the aromatic ring center
    pyrimidine_center = np.mean(
        [atom1.coord, atom2.coord, atom4.coord,
         atom5.coord, atom7.coord, atom9.coord], axis=-2
    )

    return thymine, (midpoint, pyrimidine_center)


def _get_std_uracil():
    """
    Get standard base variables for uracil.

    Returns
    -------
    standard_base : AtomArray
        Standard coordinates nomenclature of the uracil base as
        :class:`AtomArray` with nomenclature of PDB File Format V3
    coordinates : tuple (ndarray, ndarray, dtype=float)
        :class:`ndarray` containing the center according to the SCHNaP-
        paper referenced in the function ``base_pairs``,
        :class:`ndarray` containing the coordinates of the pyrimidine
        ring center
    """
    atom1 = Atom([-1.284, 4.500, 0.000], atom_name="N1",  res_name="U")
    atom2 = Atom([-1.462, 3.131, 0.000], atom_name="C2",  res_name="U")
    atom3 = Atom([-2.563, 2.608, 0.000], atom_name="O2",  res_name="U")
    atom4 = Atom([-0.302, 2.397, 0.000], atom_name="N3",  res_name="U")
    atom5 = Atom([0.989, 2.884, 0.000],  atom_name="C4",  res_name="U")
    atom6 = Atom([1.935, 2.094, -0.001], atom_name="O4",  res_name="U")
    atom7 = Atom([1.089, 4.311, 0.000],  atom_name="C5",  res_name="U")
    atom8 = Atom([-0.024, 5.053, 0.000], atom_name="C6",  res_name="U")
    uracil = array(
        [atom1, atom2, atom3, atom4, atom5, atom6, atom7, atom8]
    )

    # Get the midpoint between the N3 and C6 atoms
    midpoint = np.mean([atom4.coord, atom8.coord], axis=-2)
    # Calculate the coordinates of the aromatic ring center
    pyrimidine_center = np.mean(
        [atom1.coord, atom2.coord, atom4.coord,
         atom5.coord, atom7.coord, atom8.coord], axis=-2
    )

    return uracil, (midpoint, pyrimidine_center)


_std_adenine, _std_adenine_ring_centers  = _get_std_adenine()
_std_cytosine, _std_cytosine_ring_centers = _get_std_cytosine()
_std_guanine, _std_guanine_ring_centers = _get_std_guanine()
_std_thymine, _std_thymine_ring_centers = _get_std_thymine()
_std_uracil, _std_uracil_ring_centers = _get_std_uracil()

_adenine_containing_nucleotides = ["A", "DA"]
_thymine_containing_nucleotides = ["T", "DT"]
_cytosine_containing_nucleotides = ["C", "DC"]
_guanine_containing_nucleotides = ["G", "DG"]
_uracil_containing_nucleotides = ["U", "DU"]


def base_stacking(atom_array, min_atoms_per_base=3):
    """
    Find pi-stacking interactions between aromatic rings
    in nucleic acids.
    The presence of base stacking is assumed if the following criteria
    are met [1]_:
    (i) Distance between aromatic ring centers <=4.5 Å
    (ii) Angle between the ring normal vectors <=23°
    (iii) Angle between normalized distance vector between two ring
          centers and both bases' normal vectors <=40°
    Parameters
    ----------
    atom_array : AtomArray
        The :class:`AtomArray` to find stacked bases in.
    min_atoms_per_base : integer, optional (default: 3)
        The number of atoms a nucleotides' base must have to be
        considered a candidate for a stacking interaction.
    Returns
    -------
    stacked_bases : ndarray, dtype=int, shape=(n,2)
        Each row is equivalent to one pair of stacked bases and
        contains the indices to the first atom for each one of both
        paired residues.
    Notes
    -----
    Please note that ring normal vectors are assumed to be equal to the
    base normal vectors.

    Examples
    --------
    Compute the stacking interactions for a DNA-double-helix (PDB ID
    1BNA):
    >>> from os.path import join
    >>> dna_helix = load_structure(join(path_to_structures, "1bna.pdb"))
    >>> stacking_interactions = base_stacking(dna_helix)
    >>> print(dna_helix[stacking_interactions].res_id)
    [[ 1  2]
     [ 2  3]
     [ 3  4]
     [ 4  5]
     [ 5  6]
     [ 6  7]
     [ 7  8]
     [ 8  9]
     [ 9 10]
     [11 12]
     [14 15]
     [15 16]
     [16 17]
     [17 18]
     [18 19]
     [19 20]
     [20 21]
     [21 22]
     [22 23]
     [23 24]]

    References
    ----------
    .. [1] HA Gabb, SR Sanghani and CH Robert et al.,
       "Finding and visualizing nucleic acid base stacking"
       J Mol Biol Graph, 14(1), 6-11 (1996).
    """
    # Get the stacking candidates according to a N/O cutoff distance,
    # where each base is identified as the first index of its respective
    # residue
    c1_mask = filter_nucleotides(atom_array) & (atom_array.atom_name == "C1'")
    stacking_candidates, _ = _get_proximate_residues(atom_array, c1_mask, 15)

    # Contains the plausible pairs of stacked bases
    stacked_bases = []

    # Get the residue masks for each residue
    base_masks = get_residue_masks(atom_array, stacking_candidates.flatten())

    # Group every two masks together for easy iteration (each 'row' is
    # respective to a row in ``stacking_candidates``)
    base_masks = base_masks.reshape(
        (stacking_candidates.shape[0], 2, atom_array.shape[0])
    )

    for (base1_index, base2_index), (base1_mask, base2_mask) in zip(
        stacking_candidates, base_masks
    ):
        bases = (atom_array[base1_mask], atom_array[base2_mask])

        # A list containing ndarray for each base with transformed
        # vectors from the standard base reference frame to the
        # structures' coordinates. The layout is as follows:
        #
        # [Origin coordinates]
        # [Base normal vector]
        # [SCHNAaP origin coordinates]
        # [Aromatic Ring Center coordinates]
        transformed_std_vectors = [None] * 2

        # Generate the data necessary for analysis of each base.
        for i in range(2):
            base_tuple = _match_base(bases[i], min_atoms_per_base)

            if(base_tuple is None):
                break

            transformed_std_vectors[i] = base_tuple

        normal_vectors = np.vstack((transformed_std_vectors[0][1],
                                    transformed_std_vectors[1][1]))
        aromatic_ring_centers = [transformed_std_vectors[0][3:],
                                        transformed_std_vectors[1][3:]]

        # Check if the basepairs are stacked.
        stacked = _check_base_stacking(aromatic_ring_centers, normal_vectors)

        # If a stacking interaction is found, append the first indices
        # of the bases´'residues to the output.
        if stacked:
            stacked_bases.append((base1_index, base2_index))

    return np.array(stacked_bases)


def base_pairs(atom_array, min_atoms_per_base = 3, unique = True):
    """
    Use DSSR criteria to find the basepairs in an :class:`AtomArray`.

    The algorithm is able to identify canonical and non-canonical
    base pairs. between the 5 common bases Adenine, Guanine, Thymine,
    Cytosine, and Uracil bound to Deoxyribose and Ribose.
    Each Base is mapped to the 5 common bases Adenine, Guanine, Thymine,
    Cytosine, and Uracil in a standard reference frame described in
    [1]_ using :func:`map_nucleotide()`.

    The DSSR Criteria are as follows [2]_ :

    (i) Distance between base origins <=15 Å

    (ii) Vertical separation between the base planes <=2.5 Å

    (iii) Angle between the base normal vectors <=65°

    (iv) Absence of stacking between the two bases

    (v) Presence of at least one hydrogen bond involving a base atom

    Parameters
    ----------
    atom_array : AtomArray
        The :class:`AtomArray` to find basepairs in.
    min_atoms_per_base : integer, optional (default: 3)
        The number of atoms a nucleotides' base must have to be
        considered a candidate for a basepair.
    unique : bool, optional (default: True)
        If ``True``, each base is assumed to be only paired with one
        other base. If multiple pairings are plausible, the pairing with
        the most hydrogen bonds is selected.

    Returns
    -------
    basepairs : ndarray, dtype=int, shape=(n,2)
        Each row is equivalent to one basepair and contains the first
        indices of the residues corresponding to each base.

    Notes
    -----
    The bases from the standard reference frame described in [1]_ were
    modified such that only the base atoms are implemented. Sugar atoms
    (specifically C1') were disregarded, as nucleosides such as PSU do
    not posess the usual N-glycosidic linkage, thus leading to
    inaccurate results.

    The vertical separation is implemented as the scalar
    projection of the distance vectors between the base origins
    according to [3]_ onto the averaged base normal vectors.

    The presence of base stacking is assumed if the following criteria
    are met [4]_:

    (i) Distance between aromatic ring centers <=4.5 Å

    (ii) Angle between the ring normal vectors <=23°

    (iii) Angle between normalized distance vector between two ring
          centers and both bases' normal vectors <=40°

    Please note that ring normal vectors are assumed to be equal to the
    base normal vectors.

    For structures without hydrogens the accuracy of the algorithm is
    limited as the hydrogen bonds can be only checked be checked for
    plausibility.
    A hydrogen bond is considered as plausible if a cutoff of 3.6 Å
    between N/O atom pairs is met. 3.6Å was chosen as hydrogen bonds are
    typically 1.5-2.5Å in length. N-H and O-H bonds have a length of
    1.00Å and 0.96Å respectively. Thus, including some buffer, a 3.6Å
    cutoff should cover all hydrogen bonds.

    Examples
    --------
    Compute the basepairs for the structure with the PDB id 1QXB:

    >>> from os.path import join
    >>> dna_helix = load_structure(join(path_to_structures, "1qxb.cif"))
    >>> basepairs = base_pairs(dna_helix)
    >>> print(dna_helix[basepairs].res_name)
    [['DC' 'DG']
     ['DG' 'DC']
     ['DC' 'DG']
     ['DG' 'DC']
     ['DA' 'DT']
     ['DA' 'DT']
     ['DT' 'DA']
     ['DT' 'DA']
     ['DC' 'DG']
     ['DG' 'DC']
     ['DC' 'DG']
     ['DG' 'DC']]

    References
    ----------

    .. [1] WK Olson, M Bansal and SK Burley et al.,
       "A standard reference frame for the description of nucleic acid
       base-pair geometry."
       J Mol Biol, 313(1), 229-237 (2001).

    .. [2] XJ Lu, HJ Bussemaker and WK Olson,
       "DSSR: an integrated software tool for dissecting the spatial
       structure of RNA."
       Nucleic Acids Res, 43(21), e142 (2015).

    .. [3] XJ Lu, MA El Hassan and CA Hunter,
        "Structure and conformation of helical nucleic acids: analysis
        program (SCHNAaP)."
        J Mol Biol, 273, 668-680 (1997).

    .. [4] HA Gabb, SR Sanghani and CH Robert et al.,
       "Finding and visualizing nucleic acid base stacking"
       J Mol Biol Graph, 14(1), 6-11 (1996).
    """

    # Get the nucleotides for the given atom_array
    nucleotides_boolean = filter_nucleotides(atom_array)

    # Disregard the phosphate-backbone
    non_phosphate_boolean = (
        ~ np.isin(
            atom_array.atom_name,
            ["O5'", "P", "OP1", "OP2", "OP3", "HOP2", "HOP3"]
        )
    )

    # Combine the two boolean masks
    boolean_mask = np.logical_and(nucleotides_boolean, non_phosphate_boolean)

    # Get only the nucleosides
    nucleosides = atom_array[boolean_mask]


    # Get the basepair candidates according to a N/O cutoff distance,
    # where each base is identified as the first index of its respective
    # residue
    n_o_mask = np.isin(nucleosides.element, ["N", "O"])
    basepair_candidates, n_o_matches = _get_proximate_residues(
        nucleosides, n_o_mask, 3.6
    )

    # Contains the plausible basepairs
    basepairs = []
    # Contains the number of hydrogens for each plausible basepair
    basepairs_hbonds = []

    # Get the residue masks for each residue
    base_masks = get_residue_masks(nucleosides, basepair_candidates.flatten())

    # Group every two masks together for easy iteration (each 'row' is
    # respective to a row in ``basepair_candidates``)
    base_masks = base_masks.reshape(
        (basepair_candidates.shape[0], 2, nucleosides.shape[0])
    )

    for (base1_index, base2_index), (base1_mask, base2_mask), n_o_pairs in zip(
        basepair_candidates, base_masks, n_o_matches
    ):
        base1 = nucleosides[base1_mask]
        base2 = nucleosides[base2_mask]

        hbonds =  _check_dssr_criteria(
            (base1, base2), min_atoms_per_base, unique
        )

        # If no hydrogens are present use the number N/O pairs to
        # decide between multiple pairing possibilities.
        if hbonds is None:
            # Each N/O-pair is detected twice. Thus, the number of
            # matches must be divided by two.
            hbonds = n_o_pairs/2
        if not hbonds == -1:
            basepairs.append((base1_index, base2_index))
            if unique:
                basepairs_hbonds.append(hbonds)

    basepair_array = np.array(basepairs)

    if unique:
        # Contains all non-unique basepairs that are flagged to be
        # removed
        to_remove = []

        # Get all bases that have non-unique pairing interactions
        base_indices, occurrences = np.unique(basepairs, return_counts=True)
        for base_index, occurrence in zip(base_indices, occurrences):
            if(occurrence > 1):
                # Write the non-unique basepairs to a dictionary as
                # 'index: number of hydrogen bonds'
                remove_candidates = {}
                for i, row in enumerate(
                    np.asarray(basepair_array == base_index)
                ):
                    if(np.any(row)):
                        remove_candidates[i] = basepairs_hbonds[i]
                # Flag all non-unique basepairs for removal except the
                # one that has the most hydrogen bonds
                del remove_candidates[
                    max(remove_candidates, key=remove_candidates.get)
                ]
                to_remove += list(remove_candidates.keys())
        # Remove all flagged basepairs from the output `ndarray`
        basepair_array = np.delete(basepair_array, to_remove, axis=0)

    # Remap values to original atom array
    basepair_array = np.where(boolean_mask)[0][basepair_array]
    for i, row in enumerate(basepair_array):
        basepair_array[i] = get_residue_starts_for(atom_array, row)

    return basepair_array


def _check_dssr_criteria(basepair, min_atoms_per_base, unique):
    """
    Check the DSSR criteria of a potential basepair.

    Parameters
    ----------
    basepair : tuple (AtomArray, AtomArray)
        The two bases to check the criteria for as :class:`AtomArray`.
    min_atoms_per_base : int
        The number of atoms a nucleotides' base must have to be
        considered a candidate for a basepair.
    unique : bool
        If ``True``, the shortest hydrogen bond length between the bases
        is calculated for plausible basepairs.

    Returns
    -------
    satisfied : int
        `> 0` if the basepair satisfies the criteria and `-1`,
        if it does not.
        If unique is ``True``, the number of hydrogen bonds is
        returned for plausible basepairs.
    """

    # A list containing ndarray for each base with transformed
    # vectors from the standard base reference frame to the structures'
    # coordinates. The layout is as follows:
    #
    # [Origin coordinates]
    # [Base normal vector]
    # [SCHNAaP origin coordinates]
    # [Aromatic Ring Center coordinates]
    transformed_std_vectors = [None] * 2

    # Generate the data necessary for analysis of each base.
    for i in range(2):
        transformed_std_vectors[i] = _match_base(
            basepair[i], min_atoms_per_base
        )

        if(transformed_std_vectors[i] is None):
            return -1

    origins = np.vstack((transformed_std_vectors[0][0],
                         transformed_std_vectors[1][0]))
    normal_vectors = np.vstack((transformed_std_vectors[0][1],
                                transformed_std_vectors[1][1]))
    schnaap_origins = np.vstack((transformed_std_vectors[0][2],
                                 transformed_std_vectors[1][2]))
    aromatic_ring_centers = [transformed_std_vectors[0][3:],
                                       transformed_std_vectors[1][3:]]

    # Criterion 1: Distance between orgins <=15 Å
    if not (distance(origins[0], origins[1]) <= 15):
        return -1

    # Criterion 2: Vertical separation <=2.5 Å
    #
    # Average the base normal vectors. If the angle between the vectors
    # is >=90°, flip one vector before averaging
    mean_normal_vector = (
        normal_vectors[0] + (normal_vectors[1] * np.sign(np.dot(
            normal_vectors[0], normal_vectors[1]
        )))
    ) / 2
    norm_vector(mean_normal_vector)
    # Calculate the distance vector between the two SCHNAaP origins
    origin_distance_vector = schnaap_origins[1] - schnaap_origins[0]

    # The scalar projection of the distance vector between the two
    # origins onto the averaged normal vectors is the vertical
    # seperation
    if not abs(np.dot(origin_distance_vector, mean_normal_vector)) <= 2.5:
        return -1

    # Criterion 3: Angle between normal vectors <=65°
    if not (np.arccos(np.dot(normal_vectors[0], normal_vectors[1]))
            >= ((115*np.pi)/180)):
        return -1

    # Criterion 4: Absence of stacking
    if _check_base_stacking(aromatic_ring_centers, normal_vectors):
        return -1

    # Criterion 5: Presence of at least one hydrogen bond
    #
    # Check if both bases came with hydrogens.
    if (("H" in basepair[0].element)
        and ("H" in basepair[1].element)):
        # For Structures that contain hydrogens, check for their
        # presence directly.
        #
        # Generate input atom array for ``hbond```
        potential_basepair = basepair[0] + basepair[1]

        # Get the number of hydrogen bonds
        bonds = len(hbond(
            potential_basepair,
            np.ones_like(potential_basepair, dtype=bool),
            np.ones_like(potential_basepair, dtype=bool)
        ))

        if bonds > 0:
            return bonds
        return -1

    else:
        # If the structure does not contain hydrogens return None
        return None


def _check_base_stacking(aromatic_ring_centers, normal_vectors):
    """
    Check for base stacking between two bases.

    Parameters
    ----------
    aromatic_ring_centers : list [ndarray, ndarray]
        A list with the aromatic ring center coordinates as
        :class:`ndarray`. Each row represents a ring center.
    normal_vectors : ndarray shape=(2, 3)
        The normal vectors of the bases.

    Returns
    -------
    base_stacking : bool
        ``True`` if base stacking is detected and ``False`` if not
    """

    # Contains the normalized distance vectors between ring centers less
    # than 4.5 Å apart.
    normalized_distance_vectors = []

    # Criterion 1: Distance between aromatic ring centers <=4.5 Å
    wrong_distance = True
    for ring_center1 in aromatic_ring_centers[0]:
        for ring_center2 in aromatic_ring_centers[1]:
            if (distance(ring_center1, ring_center2) <= 4.5):
                wrong_distance = False
                normalized_distance_vectors.append(ring_center2 - ring_center1)
                norm_vector(normalized_distance_vectors[-1])
    if wrong_distance:
        return False

    # Criterion 2: Angle between normal vectors or its supplement <=23°
    normal_vectors_angle = np.rad2deg(
        np.arccos(np.dot(normal_vectors[0], normal_vectors[1]))
    )
    if (normal_vectors_angle >= 23) and (normal_vectors_angle <= 157):
        return False

    # Criterion 3: Angle between one normalized distance vector and
    # each of the bases' normal vector or supplement <=40°
    for normal_vector in normal_vectors:
        for normalized_dist_vector in normalized_distance_vectors:
            dist_normal_vector_angle = np.rad2deg(
                np.arccos(np.dot(normal_vector, normalized_dist_vector))
            )
            if ((dist_normal_vector_angle >= 40) and
                (dist_normal_vector_angle <= 120)):
                return False

    return True


def _match_base(nucleotide, min_atoms_per_base):
    """
    Match the nucleotide to a corresponding standard base reference
    frame.

    Parameters
    ----------
    nucleotide : AtomArray
        The nucleotide to be matched to a standard base.
    min_atoms_per_base : integer
        The number of atoms a base must have to be considered a
        candidate for a basepair.

    Returns
    -------
    vectors : ndarray, dtype=float, shape=(n,3)
        Transformed standard vectors, origin coordinates, base normal
        vector, aromatic ring center coordinates.
    """

    # Standard vectors containing the origin and the base normal vectors
    vectors = np.array([[0, 0, 0], [0, 0, 1]], np.float)

    # Map the nucleotide to a reference base
    base_tuple = map_nucleotide(nucleotide, min_atoms_per_base)

    if base_tuple is None:
        return None

    one_letter_code, _ = base_tuple

    if (one_letter_code == 'A'):
        std_base = _std_adenine
        std_ring_centers = _std_adenine_ring_centers
    elif (one_letter_code == 'T'):
        std_base = _std_thymine
        std_ring_centers = _std_thymine_ring_centers
    elif (one_letter_code == 'C'):
        std_base = _std_cytosine
        std_ring_centers = _std_cytosine_ring_centers
    elif (one_letter_code == 'G'):
        std_base = _std_guanine
        std_ring_centers = _std_guanine_ring_centers
    elif (one_letter_code == 'U'):
        std_base = _std_uracil
        std_ring_centers = _std_uracil_ring_centers

    # Add the ring centers to the array of vectors to be transformed.
    vectors = np.vstack((vectors, std_ring_centers))

    # Select the matching atoms of the nucleotide and the standard base
    nucleotide_matched = nucleotide[
        np.isin(nucleotide.atom_name, std_base.atom_name)
    ]
    std_base_matched = std_base[
        np.isin(std_base.atom_name, nucleotide.atom_name)
    ]

    # Reorder the atoms of the nucleotide to obtain the standard RCSB
    # PDB atom order
    nucleotide_matched = nucleotide_matched[standardize_order(
        nucleotide_matched
    )]

    # Match the selected std_base to the base.
    _, transformation = superimpose(nucleotide_matched, std_base_matched)

    # Transform the vectors
    trans1, rot, trans2 = transformation
    vectors += trans1
    vectors  = np.dot(rot, vectors.T).T
    vectors += trans2
    # Normalize the base-normal-vector
    vectors[1,:] = vectors[1,:]-vectors[0,:]
    norm_vector(vectors[1,:])

    return vectors

def map_nucleotide(residue, min_atoms_per_base=3, rmsd_cutoff=0.28):
    """
    Maps a nucleotide to one of the 5 common bases Adenine, Guanine,
    Thymine, Cytosine, and Uracil. If one of those bases bound to
    Deoxyribose and Ribose is detected as input, the corresponding one-
    letter-code (A, G, T, C, U) is returned.

    If a different nucleotide is given, it is mapped to the best best
    fitting base using the algorithm described below.

    (i) The number of matching atom names with the reference bases is
        counted. If the number of matching atoms with all reference
        bases is less than the specified ``min_atoms_per_base``
        (default 3) the nucleotide cannot be mapped and ``None```is
        returned.

    (ii) The bases with maximum number of matching atoms are selected
         and superimposed with each reference. The base with lowest RMSD
         is chosen. If the RMSD is more than the specified
         ``rmsd_cutoff`` (default 0.28) the nucleotide cannot be mapped
         and ``None```is returned.

    Parameters
    ----------
    residue : AtomArray
        The nucleotide to be mapped.
    min_atoms_per_base : integer, optional (default: 3)
        The number of atoms the residue must have in common with the
        reference.
    rmsd_cutoff : float, optional (default: 0.28)
        The maximum RSMD that is allowed for a mapping to occur.

    Returns
    -------
    one_letter_code : string
        The one-letter-code of the mapped base
    exact_match : boolean
        Wether or not the residue name exactly matches with the
        reference.
    """
    # Check if the residue is a 'standard' nucleotide
    if residue.res_name[0] in (_thymine_containing_nucleotides +
        _guanine_containing_nucleotides + _uracil_containing_nucleotides
        + _cytosine_containing_nucleotides + _adenine_containing_nucleotides
    ):
        return residue.res_name[0][-1], True

    # List of the standard bases for easy iteration
    std_base_list = [
        _std_adenine, _std_thymine, _std_cytosine, _std_guanine,
        _std_uracil
    ]

    # The number of matched atoms for each 'standard' base
    matched_atom_no = []

    # Count the number of matching atoms with the reference bases
    for ref_base in std_base_list:
        matched_atom_no.append(np.sum(
            np.isin(ref_base.atom_name, residue.atom_name)
        ))

    if max(matched_atom_no) < min_atoms_per_base:
        warnings.warn(
            f"Base with res_id {residue.res_id[0]} and chain_id "
            f"{residue.chain_id[0]} has an overlap with the reference "
            f"bases which is less than {min_atoms_per_base} atoms. "
            f"Unable to map nucleotide.",
            IncompleteStructureWarning
        )
        return None

    # The one letter code of the best matching reference base
    best_base = None

    # Iterate through the reference bases with the maximum number of
    # matching atoms
    for ref_base in np.array(std_base_list)[
        np.array(matched_atom_no) == max(matched_atom_no)
    ]:
        # Copy the residue as the res_name property of the ``AtomArray``
        # has to be modified for later function calls.
        nuc = residue.copy()

        # Select the matching atoms of the nucleotide and the reference
        # base
        nuc = nuc[
            np.isin(nuc.atom_name, ref_base.atom_name)
        ]
        ref_base_matched = ref_base[
            np.isin(ref_base.atom_name, nuc.atom_name)
        ]

        # Set the res_name property to the same as the reference base.
        # This is a requirement for ``standardize_order``
        nuc.res_name = ref_base_matched.res_name
        # Reorder the atoms of the nucleotide to obtain the standard
        # RCSB PDB atom order. If a residue contains multiple Atoms with
        # the same ``atom_name`` an exception is thrown by
        # ``standardize_order``. The Exception is caught and the
        # selected reference is disregarded
        try:
            nuc = nuc[standardize_order(nuc)]
        except Exception:
            continue

        # Superimpose the nucleotide to the reference base
        fitted, _ = superimpose(ref_base_matched, nuc)

        # If the RMSD is lower than the specified cutoff or better than
        # a previous found reference, the current reference is selected
        # as best base
        if(rmsd(fitted, ref_base_matched) < rmsd_cutoff):
            rmsd_cutoff = rmsd(fitted, ref_base_matched)
            best_base = ref_base_matched.res_name[0][-1]

    if best_base is None:
        warnings.warn(
            f"Base Type {residue.res_name[0]} not supported. "
            f"Unable to check for basepair",
            UnexpectedStructureWarning
        )
        return None

    return best_base, False


def _get_proximate_residues(atom_array, boolean_mask, cutoff):
    """
    Filter for residue pairs based on the distance between selected
    atoms.

    Parameters
    ----------
    atom_array : AtomArray, shape=(n,)
        The :class:`AtomArray`` to find basepair candidates in.
    boolean_mask : ndarray, dtype=bool, shape=(n,)
        The selection of atoms.
    cutoff : integer
        The maximum distance between the atoms of the two residues.

    Returns
    -------
    pairs : ndarray, dtype=int, shape=(n,2)
        Contains the basepair candidates. Each row is equivalent to one
        potential basepair. bases are represented as the first indices
        of their corresponding residues.
    count : ndarray, dtype=int, shape=(n,)
        The number of atom pairs between the residues within the
        specified cutoff
    """

    # Get the indices of the atoms that are within the maximum cutoff
    # of each other
    indices = CellList(
        atom_array, cutoff, selection=boolean_mask
    ).get_atoms(atom_array.coord[boolean_mask], cutoff)

    # Loop through the indices of potential partners
    pairs = []
    for candidate, partners in zip(np.argwhere(boolean_mask)[:, 0], indices):
        for partner in partners:
            if partner != -1:
                pairs.append((candidate, partner))

    # Get the residue starts for the indices of the candidate/partner
    # indices.
    pairs = np.array(pairs)
    basepair_candidates_shape = pairs.shape
    pairs = get_residue_starts_for(
        atom_array, pairs.flatten()
    ).reshape(basepair_candidates_shape)

    # Remove candidates where the pairs are from the same residue
    pairs = np.delete(
        pairs, np.where(
            pairs[:,0] == pairs[:,1]
        ), axis=0
    )
    # Sort the residue starts for each pair
    for i, candidate in enumerate(pairs):
        pairs[i] = sorted(candidate)
    # Make sure each pair is only listed once, count the occurrences
    pairs, count = np.unique(pairs, axis=0, return_counts=True)

    return pairs, count


def _filter_atom_type(atom_array, atom_names):
    """
    Get all atoms with specified atom names.

    Parameters
    ----------
    atom_array : AtomArray
        The :class:`AtomArray` to filter.
    atom_names : array_like
        The desired atom names.

    Returns
    -------
    filter : ndarray, dtype=bool
        This array is ``True`` for all indices in the :class:`AtomArray`
        , where the atom has the desired atom names.
    """
    return (np.isin(atom_array.atom_name, atom_names)
            & (atom_array.res_id != -1))
