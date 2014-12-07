
#' importReaderData
#'
#' @title Importing Data from Microtiter Plate Readers
#' @description This function is the main dispatcher function for reading several file formats into dataframes.
#' Currently supported devices:
#'   BMG Readers (e.g. Omega ) - device='omega'
#'   Thermo Scientific (e.g. Varioskan) - device='varioskan'
#' Currently supported formats (method):
#'     SPabs : Single point absorption measurement (Omega, Varioskan)
#'     SPabsMatr: Single point absorption measurement in Matrix Layout format (Omega)
#'     SPfl:   Single point fluorescense measurement (Varioskan)
#'     KINabs: Kinetic absorption measurement (Varioskan)
#' Pathlength correction (PLC) is currently based on height and volume of a well/cylinder formula  
#' @param    filename/pattern (string)
#' @param    path (string)
#' @param    method (string) - one of the above described methods 
#' @param    device (string) - one of the above mentioned devices
#' @param    layout (boolean) - automatically read plate layout file
#' @param    PLC    (boolena) - automatically calculate pathlength correction
#' @return data frame with reader data
#' @keywords plate readers
#' @examples
#'   kin_df <- importReaderData("_KINabs_245_265_", method="KINabs", device='varioskan', layout=FALSE, PLC=TRUE)
#' 
#' @note todo: debugging, runtime optimization, error handling
#' @note filename patterns e.g.   
#' @export 

importReaderData <- function( filename = "", path=".", device='omega', method='SPabs',
                              wavelength=0, barcode="0000", layout=TRUE, PLC=FALSE )
{
  if(filename == "" ) {print("Error: no filename specified for importReaderData !"); return()}
  help_info <- "please type: ?importReaderData"
  # creating a list of all files in current directory with the file ending .dat
  # ^0483_ #_OD600_ "_KINabsMW_245_265_" _SPfl_488_530_

  file_list <- list.files(path = path, pattern = filename, all.files = FALSE,
                           full.names = FALSE, recursive = FALSE,
                           ignore.case = FALSE, include.dirs = FALSE)
  
  switch(device,
         omega={ switch(method,
                        SPabs={ reader_data <- omegaSPabs(file_list) },
                        SPabsMatr={ reader_data <- omegaSPabsMatr(file_list) },
                        {cat(method, " - method not found for Omega device\n"); return(help_info); } # default
                        )
                },
         varioskan={ switch(method,
                           SPabs={ print("to be implemented") },
                           SPfl={reader_data <- varioskanSPfl(file_list[1],barcode)},
                           KINabs={reader_data <- varioskanKinAbs(file_list[1])},
                           {cat(method, " - method not found Varioskan device\n"); return(help_info); }
                           )
                   },
         {cat(device, "- no or wrong device specified. Current devices: omega, varioskan\n"); return(help_info); }
         )
  
  # auto adding plate layout information
  if( layout ) reader_data <- addPlateLayout(reader_data, barcode)
  
  # **** optical pathlength correction
  # liquid volume in ml, radius in cm
  liquid_volume <- 0.2
  well_radius <- 0.34
  pathlen_fac <- pathlengthCorrectionFactor(liquid_volume=liquid_volume,
                                            well_radius=well_radius)

  if (PLC) reader_data$Value <- reader_data$Value * pathlen_fac
  
  return(reader_data)
}

#' pathlengthCorrectionFactor
#'
#' @title generating a simple pathlenght correction factor
#' @description generating a simple pathlenght correction factor based on volume and radius of a cylinder
#' @param liquid_volume=0.2, well_radius=0.34
#' @keywords plate readers
#' @export 
#' @examples
#'     pl_factor <- pathlengthCorrectionFactor(liquid_volume=0.2, well_radius=0.34)
#' 

pathlengthCorrectionFactor<-function(liquid_volume=0.2, well_radius=0.34)
{
  optical_pathlength = liquid_volume / (pi * well_radius^2)
  pathlength_correction_factor = 1/optical_pathlength  #signif((1/optical_pathlength),digits=3)
  
  return(pathlength_correction_factor)
}

#' genWellNumbers
#'
#' @title Well Number Generator
#' @description Generator for microtiter plate well coordinates
#' @param padding
#' @return factors of well numbers
#' @keywords plate readers
#' @export 
#' @examples
#'   genWellNumbers(padding=1)
#'    ->  A1, A2, ...., H12
#'   genWellNumbers(padding=3)
#'    -> A001, A002, ..., H012

genWellNumbers <- function(padding = 2)
{
  well_numbers <- sapply(LETTERS[1:8], 
                         function(x) sprintf(paste("%s%0",padding,"d", sep=""), x, c(1:12)) )
  return(as.factor(well_numbers)) 
}

#' loadPlateLayout
#'
#' @title Reading Plate Layout Information from plate layout file
#' @param reader_df, barcode="0000", set_Value_NA=TRUE, set_Slope_NA=FALSE
#' @keywords plate readers
#' @export 
#' @examples
#'   addPlateLayout(reader_df, barcode="0000", set_Value_NA=TRUE, set_Slope_NA=FALSE)
#' 

loadPlateLayout <- function(barcode="0000", as_list=FALSE)
{
  file_pattern = paste("0*",barcode,"_plate_layout.*csv",sep="")
  print(file_pattern)
  layout_filename <- list.files(path = ".", pattern = file_pattern  , all.files = FALSE,
                            full.names = FALSE, recursive = FALSE,
                            ignore.case = FALSE, include.dirs = FALSE)[1]
 
  #reading file only once
  if (is.na(layout_filename) ) {print("ERROR (loadPlateLayout): no layout file found"); return(FALSE) }
    else data_file <- readLines(layout_filename,encoding= "UTF-8")
  # reading time
  layout_description <- grep('Description:',data_file, value=TRUE)
  print(layout_description )
  # check errors !
  if(as_list ){
    descr_str <- strsplit(layout_description, split=":")[[1]][2]
    description <- strsplit(descr_str, split="\"")[[1]][1]
  
  
  layout_barcodes <- grep('# Barcodes:',data_file, value=TRUE)
  if( layout_barcodes != character(0)) {
     bc_str <- strsplit(layout_barcodes, split=":")[[1]][2]
     bc_str <- strsplit(bc_str, split="\"")[[1]][1]
     bc_str_vec <- strsplit(bc_str, split=";")[[1]]
  }
  }
  raw_layout <- read.csv(textConnection(data_file), header=TRUE, row.names=1, stringsAsFactors=TRUE, 
                         sep=",", encoding="UTF-8", comment.ch="#")
  well_df <- NULL
  well_info <- function(raw_well_info)
  {
    wi <- strsplit(raw_well_info, ":")[[1]] 
    temp_df <- data.frame('Type'=as.factor(wi[1]), 'Description'=wi[2] )
    well_df <<- rbind(well_df, temp_df )
  }
  invisible( apply(raw_layout, c(2,1), well_info ))

  well_df$Well=genWellNumbers()

  if (as_list) {
    return(list('barcodes'=barcode_vec, 'description'=description, 'layout'=well_df))
  }
  else 
  return(well_df)
}


#' addPlateLayout
#'
#' @title Adding Plate Layout Information to reader data frame 
#' @param reader_df, barcode="0000", set_Value_NA=TRUE, set_Slope_NA=FALSE
#' @keywords plate readers
#' @export 
#' @examples
#'   addPlateLayout(reader_df, barcode="0000", set_Value_NA=TRUE, set_Slope_NA=FALSE)
#' @note todo : merging bug with multiple measurements per data frame (e.g. groth data)

addPlateLayout <- function(reader_df, barcode="0000", set_Value_NA=FALSE, set_Slope_NA=FALSE)
{
  # auto choose barcode
  if (barcode == "0000") barcode <- levels(reader_df$Barcode)[1]
  
  well_df <- loadPlateLayout(barcode)
  
  # remove old Type and Description
  reader_df$Type = NULL
  reader_df$Description = NULL
  
  # merging new info into original data frame
  reader_df <- merge(reader_df, well_df)
  # set values to NA in empty plates
  if(set_Value_NA) reader_df[reader_df$Type == '0',]$Value = NA
  if(set_Slope_NA) {
    reader_df[reader_df$Type == '0',]$Slope = NA
    reader_df[reader_df$Type == '0',]$Intercept = NA
  } 
  return(reader_df)
}

#' readerDF2Array
#'
#' @title converts DataFrame to an easy plottable 3D array 
#' @param reader_data_df, num=0, wavelength=0, add_zero=TRUE, use_slope=FALSE
#' @keywords plate readers
#' @export 
#' @examples
#'    readerDF2Array(reader_data_df, num=0, wavelength=0, add_zero=TRUE, use_slope=FALSE)
#' 

readerDF2Array <- function(reader_data_df, num=0, wavelength=0, add_zero=TRUE, use_slope=FALSE)
{
  if(use_slope) reader_data.value <- reader_data_df$Slope
  else {
      if( wavelength > 0) reader_data.value <- reader_data_df[reader_data_df$Wavelength == wavelength,]$Value
      else reader_data.value <- reader_data_df$Value
  }
  
  if (num == 0) {
    print("auto determine size")
    num = length(levels(reader_data_df$Num))
    reader_data_arr <- array(reader_data.value, c(12,8,num)) 
    
    #transform
    reader_data_lst <- lapply(c(1:num),function(n) t(reader_data_arr[,,n]))
  }
  else {
    reader_data_arr <- array(reader_data.value, c(12,8,num)) 
    #transform
    reader_data_lst <- lapply(c(1:num),function(n) t(reader_data_arr[,,n]))
  }
  
  # adding zeros if required
  if (add_zero) {
    reader_data_lst <- append( reader_data_lst, list(array(c(rep(0,96)),dim=c(8,12))), after=0)
  }
  
 #  return(array(unlist(full_data_lst),c(8,12,num_meas_cycles)))
 return(array(unlist(reader_data_lst),c(8,12,length(reader_data_lst))))
 #return(reader_data_lst)
}

lmDF2ArrayOLD <- function(lin_mod_df)
{
  slope_data <- as.numeric(lin_mod_df['Slope',])
  #slope_data_na <- slope_data
  #slope_data_na[ctrl_wells] = NA
  #slope_data_scaled <- slope_data * 40
  
  slope_data_arr <- t(array(slope_data,dim=c(12,8)))
  
  # adding zeros if required
  full_slope_data <- list()
  full_slope_data[[1]] <- array(c(rep(0,96)),dim=c(8,12))
  full_slope_data[[2]] <- slope_data_arr
  
  return( array(unlist(full_slope_data),c(8,12,2)))
}

#' omegaSPabsMatr
#'
#' @title BMG Omega: Singlepoint absorption measurement with multiple wavelengths - old file formats (matrix)
#' @param filename_list
#' @keywords plate readers
#' @export 
#' @note todo: temperature, shaking, num flashes
#' @examples
#'   omegaSPabsMatr(filename_list)
#' 
omegaSPabsMatr <- function(filename_list)
{
  print(cat("reading Omega SPabs- new old : ", filename_list))
  
  read_all_data <- function(filename)
  {  
    table_offset = 4

    #reading file only once  ?collapse=" ",
    data_file <- readLines(filename,encoding= "UTF-8")
    # reading time
    raw_date<- grep('Date:',data_file, value=TRUE)
    # %I hours in 1-12, %p AM/PM
    date_time <- strptime(raw_date, format = "Date: %Y/%m/%d Time: %I:%M:%S %p", tz = "CET")
    # reading barcode of plate  'ID1:.*ID2:'
    barcode <- strsplit(grep('ID1:.*', data_file, value=TRUE), " ")[[1]][2]
    # finding wavelengths
    wavelength_lines <- grep('\\d{3}nm',data_file, value=TRUE)
    # removing "nm" and gain values  from wavelengths
    wavelengths <- sub("nm.*", "", sub(".*: ", "",  wavelength_lines))
    # finding all data tables
    abs_table_start_rows <- grep('Chromatic', data_file)
    
    readMultipleWavelengthData <- function(wavelength)
    {
      # reading absorption data
      table_start_row <- abs_table_start_rows[i] + table_offset

      temp_tab <- read.table(textConnection(data_file), skip = table_start_row, header=FALSE, row.names=1, nrows=8)  
      
      raw_tab <- data.frame('Value'=c(apply(temp_tab, 1, function(x) x )))
      # transform data frame
    
      raw_tab$Well <- genWellNumbers()
      raw_tab$Barcode <- as.factor(barcode)
      raw_tab$Num <- as.factor(file_num)
      raw_tab$DateTime <- date_time
      raw_tab$Type <- as.factor("sample")
      raw_tab$Wavelength <- wavelength 
      
      i <<- i+1 
      full_abs_df <<- rbind(full_abs_df,raw_tab)
    }
    
    i <- 1  # "static" variable for iterating through table starts
    abs_data <- sapply(wavelengths,readMultipleWavelengthData )
    file_num <<- file_num + 1
  } 
  
  file_num <- 1  # counter for multiple file reads 
  full_abs_df <- NULL
  sapply(filename_list, read_all_data )
  
  return(full_abs_df[order(full_abs_df$Num),])
}

#' omegaSPabs
#'
#' @title BMG Omega: Singlepoint absorption measurement with multiple wavelengths - new file format (lists)
#' @param filename_list
#' @keywords plate readers
#' @export 
#' @examples
#'    omegaSPabs(filename_list)
#' 
#' @note num_wells needs to be soft-coded

omegaSPabs <- function(filename_list)
{
  print("reading Omega SPabs - new")
  
  read_all_data <- function(filename)
  {  
    table_offset = 2
    num_wells=96
    #reading file only once  ?collapse=" ",
    data_file <- readLines(filename,encoding= "UTF-8")
    # reading time
    raw_date<- grep('Date:',data_file, value=TRUE)
    # %I hours in 1-12, %p AM/PM
    date_time <- strptime(raw_date, format = "Date: %Y/%m/%d Time: %I:%M:%S %p", tz = "CET")
    # reading barcode of plate
    barcode <- strsplit(grep('ID1:.*ID2:', data_file, value=TRUE), " ")[[1]][2]
    # finding wavelengths
    wavelength_lines <- grep('\\d{3}nm',data_file, value=TRUE)
    # removing "nm" and gain values  from wavelengths
    wavelengths <- sub("nm.*", "", sub(".*: ", "",  wavelength_lines))
    # finding all data tables
    abs_table_start_rows <- grep('Chromatic', data_file)
    
    readMultipleWavelengthData <- function(wavelength)
    {
      # reading absorption data
      table_start_row <- abs_table_start_rows[i] + table_offset
      col_names <- c('Well', 'Value')
      raw_tab <- read.table(textConnection(data_file), skip = table_start_row, header=TRUE,
                            col.names=col_names, nrows=num_wells)  
      
      raw_tab$Barcode <- as.factor(barcode)
      raw_tab$Num <- as.factor(file_num)
      raw_tab$DateTime <- date_time
      raw_tab$Type <- as.factor("sample")
      raw_tab$Wavelength <- as.factor(wavelength) 

      i <<- i+1 
      full_abs_df <<- rbind(full_abs_df,raw_tab)
    }
    
    i <- 1  # "static" variable for iterating through table starts
    abs_data <- sapply(wavelengths,readMultipleWavelengthData )
    file_num <<- file_num + 1
  } 
  
  file_num <- 1
  full_abs_df <- NULL
  sapply(filename_list, read_all_data )
  
  return(full_abs_df)
}

#' varioskanKinAbs
#'
#' @title Thermo Varioskan: Kinetic absorption measurement with multiple wavelengths - new file format (lists)
#' @param filename_list
#' @keywords plate readers
#' @export 
#' @examples
#'    varioskanKinAbs(filename_list)
#' 
#' @note todo - adding number of measurements 

varioskanKinAbs <- function(filename)
{
  cat("reading Varioskan KIN abs file: ", filename, "\n")
  num_wells = 96
  
  #reading file only once
  data_file <- readLines(filename,encoding= "UTF-8")
  num_wavelengths <- length(grep("Wavelength \\[nm\\]", data_file))
  num_readings <- as.numeric(strsplit(grep('Readings',data_file, value=TRUE)[1], "\t")[[1]][6])
  table_start_row <- grep('Photometric1',data_file)[2] + 2

  col_names <- c('Barcode', 'Well', 'Type', 'Description', 'SampleNo', 'Value', 'Time', 'Wavelength', 'Read')
  print(cat(num_readings, num_wavelengths,  num_wells))
  raw_tab <- read.table(filename, skip = table_start_row, header=FALSE, col.names=col_names,
                         nrows=num_readings * num_wavelengths * num_wells)
  raw_tab$Num <- as.factor(1) # todo - adding number of measurements 
  
  # return tab ordered after well
  raw_tab$Barcode <- as.factor(raw_tab$Barcode)
  return(raw_tab[order(raw_tab[,2]),])
}

#' varioskanSPfl
#'
#' @title Thermo Varioskan: reading all fluorescent measurements into one data frame - new file format (lists)
#' @param filename
#' @keywords plate readers
#' @export 
#' @examples
#'    varioskanSPfl(filename)
#' 
#' @note todo - adding correct number of measurements 
#' 

varioskanSPfl <- function(filename, barcode="0000")
{
  cat("reading Varioskan fl file: ", filename)
  num_wells=96
  
  # finding start of measurement/run
  start_time <- grep('Run started',readLines(filename)) - 1
  raw_date = read.table(filename, skip = start_time, nrows=1, header=FALSE, 
                        comment.char="+", stringsAsFactors=FALSE)
  date_time <- strptime(paste(raw_date$V3,raw_date$V4), format = "%m/%d/%Y %H:%M:%S", tz = "CET")
  
  table_start_row <- grep('Fluorometric1',readLines(filename))[2] + 2
  col_names <- c('Barcode', 'Well', 'Type', 'Description', 'SampleNo', 'Value', 'Duration', 'ExWL', 'EmWL')
  raw_tab <- read.table(filename, skip = table_start_row, header=FALSE, col.names=col_names,
                        nrows=num_wells  )
  
  if( barcode == "0000" ) raw_tab$Barcode <- as.factor(raw_tab$Barcode)
  else raw_tab$Barcode <- as.factor(barcode)
  
  raw_tab$Num <- factor(1)
  raw_tab$DateTime <- date_time
  
  # return data frame ordered after wells
  return(raw_tab[order(raw_tab[,2]),])
}
