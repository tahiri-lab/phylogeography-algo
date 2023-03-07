﻿import pandas as pd
import os
import shutil
import csv
from Params import Params
from Bio.Phylo.TreeConstruction import DistanceCalculator
from Bio.Phylo.TreeConstruction import DistanceTreeConstructor
from Bio.Phylo.TreeConstruction import _DistanceMatrix
from Bio.Phylo.Consensus import *
from MultiProcessor import Multi
from Alignement import AlignSequences
from csv import writer as csv_writer
import random

bootstrapList = []
data = []


def openCSV(file):
    """
    Open and read the csv file to get the datas

    Args:
        fileName (the file with the content to read from)

    Return:
        The content of the file
    """
    df = pd.read_csv(file)
    return df


def getDissimilaritiesMatrix(df, columnWithSpecimenName, columnToSearch):
    """
    Creation of a list containing the names of specimens and minimums
    tempratures

    Args:
        df (content of CSV file)
        columnWithSpecimenName (first column of names)
        columnToSearch (column to compare with the first one)

    Return:
        The dissimilarities matrix

    """
    meteoData = df[columnToSearch].tolist()
    nomVar = df[columnWithSpecimenName].tolist()
    nbrSeq = len(nomVar)
    maxValue = 0
    minValue = 0

    # First loop that allow us to calculate a matrix for each sequence
    tempTab = []

    for e in range(nbrSeq):
        # A list that will contain every distances before normalisation
        tempList = []
        for i in range(nbrSeq):
            maximum = max(float(meteoData[e]), float(meteoData[i]))
            minimum = min(float(meteoData[e]), float(meteoData[i]))
            distance = maximum - minimum
            tempList.append(float("{:.6f}".format(distance)))

        # Allow to find the maximum and minimum value for the weather value and
        # then to add the temporary list in an array
        if maxValue < max(tempList):
            maxValue = max(tempList)
        if minValue > min(tempList):
            minValue = min(tempList)
        tempTab.append(tempList)

    # Calculate normalised matrix
    tabDf = pd.DataFrame(tempTab)
    dmDf = (tabDf - minValue) / (maxValue - minValue)
    dmDf = dmDf.round(6)

    matrix = [dmDf.iloc[i, :i + 1].tolist() for i in range(len(dmDf))]
    dm = _DistanceMatrix(nomVar, matrix)
    return dm


def leastSquare(tree1, tree2):
    """
    Method that calculates the least square distance between two trees.
    Trees must have the same number of leaves.
    Leaves must all have a twin in each tree.
    A tree must not have duplicate leaves
     x   x
    ╓╫╖ ╓╫╖
    123 312

    Args:
        tree1 (distanceTree object from biopython)
        tree2 (distanceTree object from biopython)

    Return:
        return result (double) the final distance between the two

    """
    ls = 0.00
    leaves = tree1.get_terminals()

    leavesName = list(map(lambda x: x.name, leaves))

    for i in leavesName:
        leavesName.pop(0)
        for j in leavesName:
            d1 = (tree1.distance(tree1.find_any(i), tree1.find_any(j)))
            d2 = (tree2.distance(tree2.find_any(i), tree2.find_any(j)))
            ls += (abs(d1 - d2))
    return ls


def drawTreesmake(trees, p):
    """
    Function that will draw the trees for each climatic variable.
    The DistanceTreeConstructor object is transformed to Newick format and
    loaded as a toytree MulTitree object. Some stylings are applied and the
    resulting trees are drawed into a .pdf in the viz/ dir.

    Args:
        trees (Dictionnary of DistanceTreeConstructor object with climatic
        variable for keys)
        p (Params object)

    """
    treesNewick = {}
    toytrees = []

    for k, v in trees.items():
        treesNewick[k] = v.format('newick')
        ttree = toytree.tree(treesNewick[k], tree_format=1)
        toytrees.append(ttree)
    mtree = toytree.mtree(toytrees)

    # Setting up the stylings for nodes
    for tree in mtree.treelist:
        tree.style.edge_align_style = {'stroke': 'black', 'stroke-width': 1}
        for node in tree.treenode.traverse():
            if node.is_leaf():
                node.add_feature('color', toytree.colors[7])
            else:
                node.add_feature('color', toytree.colors[1])
    colors = tree.get_node_values('color', show_root=1, show_tips=1)

    # Draw the climatic trees
    canvas, axes, mark = mtree.draw(nrows=round(len(mtree) / 5),
                                    ncols=len(mtree), height=400, width=1000,
                                    node_sizes=8, node_colors=colors,
                                    tip_labels_align=True)

    for i in range(len(mtree)):
        randColor = "#%03x" % random.randint(0, 0xFFF)
        axes[i].text(0, mtree.ntips, p.names[i + 1], style={'fill': randColor,
                                                            'font-size': '10px',
                                                            'font-weight': 'bold'
                                                            })

    toyplot.pdf.render(canvas, '../viz/climactic_trees.pdf')


def createTree(dm):
    '''
    Create a dna tree from content coming from a fasta file.

    Args:
        dm (content used to create the tree)

    Return:
        tree (the new tree)
    '''
    constructor = DistanceTreeConstructor()
    tree = constructor.nj(dm)
    return tree


def climaticPipeline(p=Params()):
    '''
    Creates a dictionnary with the climatic Trees
    Args:
        p (Params object : created if not specified)

    Return:
        trees (the climatic tree dictionnary)
    '''
    trees = {}
    df = openCSV(p.file_name)
    for i in range(1, len(p.names)):
        dm = getDissimilaritiesMatrix(df, p.names[0], p.names[i])
        trees[p.names[i]] = createTree(dm)
    return trees


def createBoostrap(msaSet: dict, p: Params):
    '''
    Create a tree structure from sequences given by a dictionnary.
    Args:
        msaSet (dictionnary with multiple sequences alignment to transform into
                trees)
        p (Params object)
    Return:
        A dictionary with the trees for each sequence
    '''
    constructor = DistanceTreeConstructor(DistanceCalculator('identity'))

    # creation of intermidiary array
    # each array is a process
    array = []
    for key in msaSet.keys():
        array.append([msaSet, constructor, key, p.bootstrapAmount])

    # multiprocessing
    print("Creating bootstrap variations with multiplyer of : ",
          p.bootstrapAmount)

    result = Multi(array, bootSingle).processingSmallData()

    # reshaping the output into a readble dictionary
    consensusTree = {}
    for i in result:
        consensusTree[i[1]] = i[0]

    return consensusTree


def bootSingle(args):
    '''
    Args:
        args (list of arguments)
    Return:
        *********TO WRITE**********
    '''
    msaSet = args[0]
    constructor = args[1]
    key = args[2]
    bootstrapAmount = args[3]

    result = bootstrap_consensus(msaSet[key], bootstrapAmount, constructor,
                                 majority_consensus)
    return [result, key]


def calculateAverageBootstrap(tree):
    '''
    Calculate if the average confidence of a tree

    Args:
        tree (The tree to get the average confidence from)
    Return :
        averageBootstrap (the average Bootstrap (confidence))
    '''
    leaves = tree.get_nonterminals()
    treeConfidences = list(map(lambda x: x.confidence, leaves))
    treeConfidences.pop(0)
    totalConfidence = 0
    for confidences in treeConfidences:
        totalConfidence += confidences
    averageBootsrap = totalConfidence / len(treeConfidences)
    return averageBootsrap


def createGeneticList(geneticTrees, p: Params):
    '''
    Create a list of Trees if the bootstrap Average is higher than
    the threshold

    Args :
        geneticTrees (a dictionnary of genetic trees)
    Return :
        geneticList (a list with the geneticTrees)
    '''
    geneticList = []
    for key in geneticTrees:
        bootstrap_average = calculateAverageBootstrap(geneticTrees[key])
        if bootstrap_average >= p.bootstrap_threshold:
            bootstrapList.append(bootstrap_average)
            geneticList.append(key)
    return geneticList


def createClimaticList(climaticTrees):
    '''
    Create a list of climaticTrees

    Args :
        climaticTrees (a dictionnary of climatic trees)
    Return :
        climaticList(a list with the climaticTrees)
    '''
    climaticList = []
    for key in climaticTrees:
        climaticList.append(key)
    return climaticList


def getData(leavesName, ls, index, climaticList, geneticList, p: Params):
    '''
    Get data from a csv file a various parameters to store into a list

    Args :
        leavesName (the list of the actual leaves)
        ls (least square distance between two trees)
        climaticList (the list of climatic trees)
        geneticList : (the list of genetic trees)
        p (Params object)
    '''
    p.file_name
    with open(p.file_name, 'r') as file:
        csvreader = csv.reader(file)
        for leave in leavesName:
            for row in csvreader:
                if row[0] == leave:
                    return [p.reference_gene_filename, climaticList[index],
                            leave, geneticList[0],
                            str(bootstrapList[0]), str(round(ls, 2))]


def writeOutputFile(data):
    '''
    Write the datas from data list into a new csv file

    Args :
        data (the list contaning the final data)
    '''
    print("Writing the output file")
    header = ['Gene', 'Phylogeographic tree', 'Name of species',
              'Position in ASM', 'Bootsrap mean', 'Least-Square distance']
    with open("output.csv", "w", encoding="UTF8") as f:
        writer = csv_writer(f)
        writer.writerow(header)
        for i in range(len(data)):
            writer.writerow(data[i])
        f.close


def filterResults(climaticTrees, geneticTrees, p: Params):
    '''
    Create the final datas from the Climatic Tree and the Genetic Tree

    Args :
        climaticTrees (the dictionnary containing every climaticTrees)
        geneticTrees (the dictionnary containing every geneticTrees)
        p (the Params object)
    '''
    # Create a list of the tree if the bootstrap is superior to the
    # bootstrap treshold
    geneticList = createGeneticList(geneticTrees, p)

    # Create a list with the climatic trees name
    climaticList = createClimaticList(climaticTrees)

    # Compare every genetic trees with every climatic trees. If the returned
    # value is inferior or equal to the (Least-Square distance) LS threshold,
    # we keep the data
    while (len(geneticList) > 0):
        leaves = geneticTrees[geneticList[0]].get_terminals()
        leavesName = list(map(lambda x: x.name, leaves))
        i = 0
        for tree in climaticTrees.keys():
            ls = leastSquare(geneticTrees[geneticList[0]],
                             climaticTrees[climaticList[i]])
            if ls is None:
                raise Exception('The LS distance is not calculable' + 'pour {aligned_file}.')
            if ls <= p.ls_threshold:
                data.append(getData(leavesName, ls, i, climaticList,
                                    geneticList, p))
            i += 1
        geneticList.pop(0)
        bootstrapList.pop(0)
    # We write the datas into an output csv file
    writeOutputFile(data)


def geneticPipeline(climaticTrees, p=Params(), alignementObject=None):
    '''
    Get the genetic Trees from the initial file datas so we
    can compare every valid tree with the climatic ones. In the
    end it calls a method that create a final csv file with all
    the data that we need for the comparison

    Args:
        climaticTrees (the dictionnary of climaticTrees)
        p (the Params object)[optionnal]
        aligneementObject (the AlignSequences object)[optionnal]
    '''
    # JUST TO MAKE THE DEBUG FILES
    if os.path.exists("./debug"):
        shutil.rmtree("./debug")
    if p.makeDebugFiles:
        os.mkdir("./debug")
    # JUST TO MAKE THE DEBUG FILES

    if alignementObject is None:
        alignementObject = AlignSequences(p)

    msaSet = alignementObject.msaSet
    geneticTrees = createBoostrap(msaSet, p)
    filterResults(climaticTrees, geneticTrees, p)
