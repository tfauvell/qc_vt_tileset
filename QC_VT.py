# ------------------------------------------------------------------------------
# QC Vector Tile PBF's
#
# Author: Tommy Fauvell @CartoRedux
#
# Inspiration:
#   FolderSizes - File Reporter: https://www.foldersizes.com
#
# Sample code:
#   os.walk generator: https://stackoverflow.com/a/20253803
#   Size converter: https://stackoverflow.com/a/14822210
#
# To do:
#   Add file check for .pbf files
#   Parameterize inputs
#   Create polygon selection sql clause
# ------------------------------------------------------------------------------
import os
import operator
import sys
import math

"""
    QC_VT.py will analyse the contents of a vector tile package (VTPK) and 
    generate a report based on the uncompressed file sizes of the .PBF files 
    found in the cache structure. Make sure to extract the contents of your
    VTPK with the 'extract package' geo-processing tool in ArcGIS Pro prior to
    running this script to analyze .PBF payload sizes vs .bundle file sizes.

    USAGE: The 'vt' parameter should be the absolute path to the 'tile' 
    directory within the extracted VTPK structure. Adjust the max_size 
    parameter as needed. 150KB is a conservative estimate based on average
    512x512 raster tile payload sizes. 
"""

vt = r'c:\<path_to_your_extracted_vtpk>\p12\tile'
max_size = 150  # KB

statsD = {}
statsD[1] = 0  # "[       0KB - 1KB"
statsD[2] = 0  # "[      1KB - 16KB"
statsD[3] = 0  # "[     16KB - 32KB"
statsD[4] = 0  # "[     32KB - 64KB"
statsD[5] = 0  # "[    64KB - 128KB"
statsD[6] = 0  # "[   128KB - 256KB"
statsD[7] = 0  # "[   256KB - 512KB"
statsD[8] = 0  # "[     512KB - 1MB"
statsD[9] = 0  # "[ larger than 1MB"

# hack to keep the size ranges printing in the correct order
statsLookUp = {}
statsLookUp[1] = "[       0KB - 1KB ]"
statsLookUp[2] = "[      1KB - 16KB ]"
statsLookUp[3] = "[     16KB - 32KB ]"
statsLookUp[4] = "[     32KB - 64KB ]"
statsLookUp[5] = "[    64KB - 128KB ]"
statsLookUp[6] = "[   128KB - 256KB ]"
statsLookUp[7] = "[   256KB - 512KB ]"
statsLookUp[8] = "[     512KB - 1MB ]"
statsLookUp[9] = "[ larger than 1MB ]"


def pretty_stats(x, y):
    """
        Convert file counts and total file counts into an ascii graph 
        indicating % of total files found.
    """
    x = float(x)
    if x == 0:
        m = 0
    else:
        m = math.trunc(math.ceil(((x/y) * 100) / 5))
    return (" [" + '#'*m + '.'*(20 - m) + "] ")


def group_size(fSize):
    """
        Group file sizes into range categories.
    """
    if fSize < 1024:
        return 1
    elif fSize < 16384:
        return 2
    elif fSize < 32768:
        return 3
    elif fSize < 65536:
        return 4
    elif fSize < 131072:
        return 5
    elif fSize < 262144:
        return 6
    elif fSize < 524288:
        return 7
    elif fSize < 1048576:
        return 8
    else:
        return 9


def convert_units(size_bytes):
    """
        Convert size in bytes to human readable file size notation.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def main():
    print "Analyzing tileset...\n"

    # generator - walk all file paths within vt
    all_files = (os.path.join(basedir, filename)
                 for basedir, dirs, files in os.walk(vt) for filename in files)

    # generator - tuples of files, sizes
    files_and_sizes = ((path, os.path.getsize(path)) for path in all_files)
    sorted_files_with_size = sorted(
        files_and_sizes, key=operator.itemgetter(1), reverse=True)
    print "Collecting statistics..."
    min_PBF = min(sorted_files_with_size, key=operator.itemgetter(1))
    max_PBF = max(sorted_files_with_size, key=operator.itemgetter(1))

    fCount = 0
    flaggedPBF = list()
    totalSize = 0
    
    for filePath in sorted_files_with_size:
        # flag large files and collect stats
        totalSize += filePath[1]
        statsD[group_size(filePath[1])] += 1
        if filePath[1]/1024 >= max_size:
            flaggedPBF.append((filePath[0], filePath[1]))
        fCount += 1
    
    print "\n--------------------------------------------------------"
    print ("TILESET STATS: \n" + str('{0:,}'.format(fCount)) + " tiles, smallest tile: " + convert_units(min_PBF[1]) +
           ", largest tile: " + convert_units(max_PBF[1]) + ", total size: " + convert_units(totalSize))
    print "[    size range   ] [  % of total files  ] # of files"

    for key, val in statsD.items():
        print (statsLookUp[key] + pretty_stats(val, fCount) + str('{0:,}'.format(val)))

    if len(flaggedPBF) >= 1:
        print "\nWARNING! Tileset contains %s tiles larger than %s KB" % (
            len(flaggedPBF), max_size)
        for key, val in flaggedPBF:
            # print f, s 'First: {0[0]}, Second: {0[1]}'.format(flag)
            print key + "  " + convert_units(val)
    else:
        print "\nNo tiles found larger than %s KB" % (max_size)
    print "--------------------------------------------------------\n"

    # end main


if __name__ == "__main__":
    main()
