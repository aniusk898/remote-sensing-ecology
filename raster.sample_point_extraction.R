####################################################################################################
#                                                                                                  #
#  raster.sample_point_extraction.R - Raster masking, cropping or reformating from command line    #
#                                                                                                  #
#                                                                                                  #
#                        Copyright: Julio Cesar Franco & Nicolas Pinel, 2019                       #
#                Research Group on Biodiversity, Evolution and Conservation (BEC)                  #
#                                       Universidad EAFIT                                          #
#                                       bec@eafit.edu.co                                           #
#                                                                                                  #
#                                         CC BY-SA v4.0                                            #
####################################################################################################
#
# Version:      0.1.0 (2019-05-15)
# R version:    3.6.0 (2019-04-26) -- "Planting of a Tree"
#
# Usage:        Rscript --vanilla raster.sample_point_extraction.R <path to config.yml file>
# 
# Config file:  The script expects as sole argument the full path to a config file in yaml format
#               as shown below. You may copy the variables below and paste into a simple text file,
#               making sure to remove the leading "#" and leading spaces from each line.
#
#
#     dir_in          : /path/to/directory/with/input/files/    # include trailing forward slash
#     dir_out         : /path/to/directory/for/output/          # include trailing forward slash
#     mask_shape_file : /shape/file/with/mask/boundaries.shp    # unless only reformating
#     process         : reformat                                # (reformat, crop or mask)
#     format_in_list  : tif                                     # extension of files to be read
#     format_out      : GTiff                                   # (ascii, GTiff, raster, CDF)
#     format_out_ext  : .tif                                    # format of the output raster
#                                                               # ( ascii = .asc ; GTiff = .tif
#                                                               # raster = .grd; CDF = .nc  )
#     output_prefix   : PrefixToAppendToOutputFiles             # appended to the created files
#     write_crs       : F                                       # boolean for writing CRS to file
#
#
####################################################################################################

args = commandArgs(trailingOnly=TRUE)

# Test if the input txt file is given, if not, return an error
if (length(args)==0) { stop("A config file must be supplied !!!", call.=FALSE) }

# load the required packages
if (!require("yaml")) install.packages("yaml")
if (!require("raster")) install.packages("raster")
if (!require("rgdal")) install.packages("rgdal")

# read configuration variables from file
config = yaml.load_file(args[1])

# load list of files
input.files <- list.files(path=config$dir_in, pattern=config$format_in_list, full.names=TRUE)

for (i.file in input.files) {
  # read each raster file
  raster.file <- raster(i.file)
  # process raster
  if (!config$process=='reformat') {
    # read the shape file
    mask.shape.file <- readOGR(config$mask_shape_file)
    mask.extent <- extent(mask.shape.file)
    # crop the raster file    
    raster.file <- crop(raster.file, mask.extent, snap='near')
    # mask if so specified
    if (!config$process=='crop') { raster.file <- mask(raster.file, mask.shape.file) }
  }
  # captura basename for each file as seed for output file name
  o.file <- tools::file_path_sans_ext(basename(i.file))
  # write resulting raster
  writeRaster(raster.file, filename= paste(config$dir_out, config$output_prefix, o.file, 
                                           config$format_out_ext, sep = ""),
              format=config$format_out, prj=config$write_crs)
}
