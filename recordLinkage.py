# ============================================================================
# Record linkage software for the COMP3430/COMP8430 Data Wrangling course, 
# 2020.
# Version 1.0
#
# Copyright (C) 2020 the Australian National University and
# others. All Rights Reserved.
#
# =============================================================================

"""Main module for linking records from two files.

   This module calls the necessary modules to perform the functionalities of
   the record linkage process.
"""

# =============================================================================
# Import necessary modules (Python standard modules first, then other modules)

import time

import loadDataset
import blocking
import comparison
import classification
import evaluation
import saveLinkResult
import pandas as pd
from tqdm import tqdm
import signal
import os
import itertools
import sys


# =============================================================================
# Variable names for loading datasets

# ******** Uncomment to select a pair of datasets **************

datasetA_name = 'assignment-data/data_wrangling_rl1.csv'
datasetB_name = 'assignment-data/data_wrangling_rl2.csv'

#datasetA_name = 'datasets/little-dirty-A-10000.csv'
#datasetB_name = 'datasets/little-dirty-B-10000.csv'

headerA_line   = True  # Dataset A header line available - True or Flase
headerB_line   = True  # Dataset B header line available - True or Flase

# Name of the corresponding file with true matching record pair

# ***** Uncomment a file name corresponding to your selected datasets *******

truthfile_name = 'assignment-data/data_wrangling_rlgt.csv'

#truthfile_name = 'datasets/little-dirty-true-matches-10000.csv'

# The two attribute numbers that contain the record identifiers
#
rec_idA_col = 0
rec_idB_col = 0

# The list of attributes to be used either for blocking or linking
#
# For the example data sets used in COMP8430 data wrangling in 2020:
#
#  0: rec_id
#  1: first_name
#  2: middle_name
#  3: last_name
#  4: gender
#  5: current_age
#  6: birth_date
#  7: street_address
#  8: suburb
#  9: postcode
# 10: state
# 11: phone
# 12: email

attrA_list = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12]
attrB_list = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12]


def main(blocking_fn, classification_fn, threshold, minthresh, weightvec, blocking_attrs, func_list, save = False):

    # ******** In lab 3, explore different attribute sets for blocking ************

    # The list of attributes to use for blocking (all must occur in the above
    # attribute lists)
    blocking_attrA_list = blocking_attrs
    blocking_attrB_list = blocking_attrs

    # ******** In lab 4, explore different comparison functions for different  ****
    # ********           attributes                                            ****

    # The list of tuples (comparison function, attribute number in record A,
    # attribute number in record B)
    #
    exact_comp_funct_list = [(comparison.exact_comp, 1, 1),  # First name
                             (comparison.exact_comp, 2, 2),  # Middle name
                             (comparison.exact_comp, 3, 3),  # Last name
                             (comparison.exact_comp, 8, 8),  # Suburb
                             (comparison.exact_comp,10,10),  # State
                             ]

    approx_comp_funct_list = [(func_list[0], 1, 1),        # First name
                              (func_list[1], 2, 2),           # Middle name
                              (func_list[2], 3, 3),   # Last name
                              (func_list[3], 7, 7),   # Address
                              (func_list[4], 8, 8),  # Suburb
                              (func_list[5],10,10),          # State
                             ]

    # =============================================================================
    #
    # Step 1: Load the two datasets from CSV files

    start_time = time.time()

    recA_dict = loadDataset.load_data_set(datasetA_name, rec_idA_col, \
                                          attrA_list, headerA_line)
    recB_dict = loadDataset.load_data_set(datasetB_name, rec_idB_col, \
                                          attrB_list, headerB_line)

    # Load data set of true matching pairs
    #
    true_match_set = loadDataset.load_truth_data(truthfile_name)

    loading_time = time.time() - start_time

    # -----------------------------------------------------------------------------
    # Step 2: Block the datasets

    def genericBlock (block_function = 'none', recA_dict = recA_dict, recB_dict = recB_dict,
                      blocking_attrA_list = blocking_attrA_list,
                      blocking_attrB_list = blocking_attrB_list):

        start_time = time.time()

        # Select one blocking technique
        if block_function == 'none':
            # No blocking (all records in one block)
            #
            resultA = blocking.noBlocking(recA_dict)
            resultB = blocking.noBlocking(recB_dict)

        if block_function == 'attr':
            # Simple attribute-based blocking
            #
            resultA = blocking.simpleBlocking(recA_dict, blocking_attrA_list)
            resultB = blocking.simpleBlocking(recB_dict, blocking_attrB_list)

        if block_function == 'soundex':
            # Phonetic (Soundex) based blocking
            #
            resultA = blocking.phoneticBlocking(recA_dict, blocking_attrA_list)
            resultB = blocking.phoneticBlocking(recB_dict, blocking_attrB_list)

        if block_function == 'slk':
            # Statistical linkage key (SLK-581) based blocking
            #
            fam_name_attr_ind = 3
            giv_name_attr_ind = 1
            dob_attr_ind      = 6
            gender_attr_ind   = 4

            resultA = blocking.slkBlocking(recA_dict, fam_name_attr_ind, \
                                              giv_name_attr_ind, dob_attr_ind, \
                                              gender_attr_ind)
            resultB = blocking.slkBlocking(recB_dict, fam_name_attr_ind, \
                                              giv_name_attr_ind, dob_attr_ind, \
                                              gender_attr_ind)

        block_time = time.time() - start_time

        # Print blocking statistics
        #
        # blocking.printBlockStatistics(resultA, resultB)

        return resultA, resultB, block_time

    blockA_dict, blockB_dict, blocking_time = genericBlock(block_function=blocking_fn)
    # -----------------------------------------------------------------------------
    # Step 3: Compare the candidate pairs

    start_time = time.time()

    sim_vec_dict = comparison.compareBlocks(blockA_dict, blockB_dict, \
                                            recA_dict, recB_dict, \
                                            approx_comp_funct_list)

    comparison_time = time.time() - start_time

    # -----------------------------------------------------------------------------
    # Step 4: Classify the candidate pairs

    def genericClassification(classification_function = 'exact', sim_vec_dict = sim_vec_dict,
                              sim_threshold = threshold, min_sim_threshold = minthresh,
                              weight_vec = weightvec, true_match_set = true_match_set):
        start_time = time.time()

        if classification_function == 'exact':
            # Exact matching based classification
            class_match_set1, class_nonmatch_set1 = \
                         classification.exactClassify(sim_vec_dict)

        if classification_function == 'simthresh':
            # Similarity threshold based classification
            #
            class_match_set1, class_nonmatch_set1 = \
                        classification.thresholdClassify(sim_vec_dict, sim_threshold)

        if classification_function == 'minsim':
            # Minimum similarity threshold based classification
            #
            class_match_set1, class_nonmatch_set1 = \
                        classification.minThresholdClassify(sim_vec_dict,
                                                            min_sim_threshold)

        if classification_function == 'weightsim':
            # Weighted similarity threshold based classification
            #
            # weight_vec = [1.0] * len(approx_comp_funct_list)

            # Lower weights for middle name and state
            #
            # weight_vec = [2.0, 1.0, 2.0, 2.0, 2.0, 1.0]

            class_match_set1, class_nonmatch_set1 = \
                        classification.weightedSimilarityClassify(sim_vec_dict,
                                                                  weight_vec,
                                                                  sim_threshold)

        if classification_function == 'dt':
            # A supervised decision tree classifier
            #
            class_match_set1, class_nonmatch_set1 = \
                      classification.supervisedMLClassify(sim_vec_dict, true_match_set)

        class_time = time.time() - start_time

        return class_match_set1, class_nonmatch_set1, class_time

    threshold = minthresh

    class_match_set, class_nonmatch_set, classification_time = genericClassification(classification_fn)

    # -----------------------------------------------------------------------------
    # Step 5: Evaluate the classification

    # Initialise dictionary of results
    dict = {}

    # Get the number of record pairs compared
    #
    num_comparisons = len(sim_vec_dict)

    # Get the number of total record pairs to compared if no blocking used
    #
    all_comparisons = len(recA_dict) * len(recB_dict)

    # Get the list of identifiers of the compared record pairs
    #
    cand_rec_id_pair_list = sim_vec_dict.keys()

    # Blocking evaluation
    #
    rr = evaluation.reduction_ratio(num_comparisons, all_comparisons)
    pc = evaluation.pairs_completeness(cand_rec_id_pair_list, true_match_set)
    pq = evaluation.pairs_quality(cand_rec_id_pair_list, true_match_set)


    # Linkage evaluation
    #
    linkage_result = evaluation.confusion_matrix(class_match_set,
                                                 class_nonmatch_set,
                                                 true_match_set,
                                                 all_comparisons)

    accuracy =    evaluation.accuracy(linkage_result)
    precision =   evaluation.precision(linkage_result)
    recall    =   evaluation.recall(linkage_result)
    fmeasure  =   evaluation.fmeasure(linkage_result)

    # print('Linkage evaluation:')
    # print('  Accuracy:    %.3f' % (accuracy))
    # print('  Precision:   %.3f' % (precision))
    # print('  Recall:      %.3f' % (recall))
    # print('  F-measure:   %.3f' % (fmeasure))
    # print('')

    linkage_time = loading_time + blocking_time + comparison_time + \
                   classification_time
    # print('Total runtime required for linkage: %.3f sec' % (linkage_time))

    # Export blocking metrics
    dict['blocking_fn'] = blocking_fn
    dict['classification_fn'] = classification_fn
    dict['threshold'] = threshold
    dict['min_thresh'] = minthresh
    dict['weight_vec'] = weightvec
    dict['blocking_attrs'] = blocking_attrs
    dict['comp_funcs'] = func_list
    dict['num_comparisons'] = num_comparisons
    dict['all_comparisons'] = all_comparisons
    # dict['cand_rec_id_pair_list'] = cand_rec_id_pair_list
    dict['rr'] = rr
    dict['pc'] = pc
    dict['pq'] = pq
    dict['blocking_time'] = blocking_time
    # dict['linkage_result'] = linkage_result
    dict['accuracy'] = accuracy
    dict['precision'] = precision
    dict['recall'] = recall
    dict['fmeasure'] = fmeasure
    dict['linkage_time'] = linkage_time

    # Save results
    if save:
        saveLinkResult.save_linkage_set('final_results.txt', class_match_set)

    # Return results
    return dict

class TimeOutError(Exception):
    pass


def handler(sig = None, frame = None):
    raise TimeOutError("Timed out!")


block_options = ['attr', 'soundex']
class_options = ['exact', 'simthresh', 'minsim', 'weightsim', 'dt']
thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
weight_vectors = [[2.0, 1.0, 2.0, 2.0, 2.0, 1.0], [1, 1, 1, 1, 1, 1]]

results_list = []

def main_iter(block, classif, threshold = 0.5, minthresh = 0.5, weightvec = [1, 1, 1, 1, 1, 1], blocking_attrs = [4,7],
              func_list = [comparison.exact_comp] * 6, timeout = 60):
    # Set the signal handler and a 5-second alarm
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        return main(block, classif, threshold, minthresh, weightvec, blocking_attrs, func_list)
    except TimeOutError:
        return {'blocking_fn': block, 'classification_fn': classif}
    signal.alarm(0)


TIMEOUT = 120

# Blocking possibilities
blocking_range = list(range(1, len(attrA_list) + 1))
blocking_possibilities = [list(itertools.combinations(blocking_range, x)) for x in blocking_range]
blocking_possibilities = [item for sublist in blocking_possibilities for item in sublist]
blocking_possibilities = [list(x) for x in blocking_possibilities]

# Comparison function possibilities
y = [comparison.jaccard_comp,
     comparison.dice_comp,
     comparison.jaro_winkler_comp,
     comparison.bag_dist_sim_comp,
     comparison.edit_dist_sim_comp,
     comparison.exact_comp]

comparison_funcs = list(itertools.product(y, repeat=6))

# Clean terminal inputs
variables_to_vary = sys.argv[1:]

# TODO: Add index of input variables
def tune_parametres(variables = variables_to_vary, random = False):
    # Print args
    print(variables_to_vary)

    # Set variables for iteration
    if 'blocking' in variables:
        # Excluding no for computational reasons add
        block_options = ['attr', 'soundex', 'slk']
    else:
        block_options = ['soundex']

    if 'classification' in variables:
        class_options = ['exact', 'simthresh', 'minsim', 'weightsim', 'dt']
    else:
        class_options = ['dt']

    if 'thresholds' in variables:
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    else:
        thresholds = [0.5]

    if 'weighted' in variables:
        weight_vectors = [[2.0, 1.0, 2.0, 2.0, 2.0, 1.0], [1, 1, 1, 1, 1, 1]]
    else:
        weight_vectors = [[1, 1, 1, 1, 1, 1]]

    if 'blocking_attrs' in variables:
        blocking_attrs = blocking_possibilities
    else:
        blocking_attrs = [[3, 7, 8]]

    if 'comparison' in variables:
        func_list = comparison_funcs
    else:
        func_list = [[comparison.bag_dist_sim_comp, comparison.jaro_winkler_comp, comparison.jaro_winkler_comp,
                      comparison.bag_dist_sim_comp, comparison.bag_dist_sim_comp, comparison.bag_dist_sim_comp]]


    for block_option in block_options:
        for class_option in tqdm(class_options):
            for func in func_list:
                if block_option == 'attr' or block_option == 'soundex':
                    # Had to repeat code here, a bit messy
                    for blocking_attr in blocking_attrs:
                        if class_option == 'simthresh':
                            for threshold1 in thresholds:
                                results_list.append(main_iter(block_option, class_option, threshold1,
                                                              blocking_attrs = blocking_attr, func_list=func, timeout = TIMEOUT))

                        elif class_option == 'minsim':
                            for threshold1 in thresholds:
                                results_list.append(main_iter(block_option, class_option, threshold1, minthresh=threshold1,
                                                              blocking_attrs = blocking_attr, func_list=func, timeout = TIMEOUT))

                        elif class_option == 'weightsim':
                            for threshold1 in thresholds:
                                for weight_vector in weight_vectors:
                                    results_list.append(main_iter(block_option, class_option, threshold1,
                                                                  weightvec=weight_vector, blocking_attrs = blocking_attr,
                                                                  func_list=func, timeout = TIMEOUT))

                        else:
                            results_list.append(main_iter(block_option, class_option, blocking_attrs = blocking_attr,
                                                          func_list=func, timeout=TIMEOUT))
                else:
                    if class_option == 'simthresh':
                        for threshold in thresholds:
                            results_list.append(
                                main_iter(block_option, class_option, threshold, blocking_attrs=None, func_list=func,
                                          timeout=TIMEOUT))

                    elif class_option == 'minsim':
                        for threshold in thresholds:
                            results_list.append(
                                main_iter(block_option, class_option, threshold, minthresh=threshold, blocking_attrs=None,
                                          func_list=func, timeout=TIMEOUT))

                    elif class_option == 'weightsim':
                        for threshold in thresholds:
                            for weight_vector in weight_vectors:
                                results_list.append(
                                    main_iter(block_option, class_option, threshold, weightvec=weight_vector,
                                              blocking_attrs=None, func_list=func, timeout=TIMEOUT))

                    else:
                        results_list.append(
                            main_iter(block_option, class_option, blocking_attrs=None, func_list=func, timeout=TIMEOUT))

    return results_list

# results = tune_parametres()
# results_df = pd.DataFrame(results)
# results_df.to_csv('-'.join(sys.argv) + '.csv')

results = main(blocking_fn = 'soundex', classification_fn = 'dt', threshold = None, minthresh = None, weightvec = None,
     blocking_attrs = [3, 7, 8], func_list = [comparison.bag_dist_sim_comp, comparison.jaro_winkler_comp,
                                              comparison.jaro_winkler_comp, comparison.bag_dist_sim_comp,
                                              comparison.bag_dist_sim_comp, comparison.bag_dist_sim_comp],
     save = True)

results_df = pd.DataFrame([results])
results_df.to_csv('final_eval.csv')

