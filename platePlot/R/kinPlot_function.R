
# helper function 
as.numeric.factor <- function(x) {as.numeric(levels(x))[x]}

#' calcAllLinModels
#'
#' @title Calculate All Linear Models of given Data Frame
#' @description Calculates all possible linar models and stores coefficients in a data frame
#' @param kin_data_df, wavelength
#' @keywords plate readers
#' @return data frame with 
#' @note relativly well runtime optimized version - don't be confused about the ugly code: it's quite fast
#' @export
#' @examples
#'  lin_mod_df <- calcAllLinModels(kin_df, wavelength=245)
#' @note todo: add barcode handling !!

calcAllLinModels <- function(kin_data_df, wavelength=0, barcode="0000")
{
  if(barcode == "0000") barcode <- levels(kin_data_df$Barcode)[1]
  col_names <- c('Well', 'Barcode', 'Num', 'Type',  'Description', 'Slope', 'Intercept')
  tmp_ma <- matrix(nrow=length(levels(kin_df$Well)),ncol=length(col_names))
  i<-1
  calc_lin_mod <- function(curr_well, wavelength)
  {
    tmp_curr_well_df <- curr_well[curr_well$Wavelength == wavelength,]
    abs1 <- tmp_curr_well_df$Value
    time1 <- tmp_curr_well_df$Time
    time1min <- time1/60
    meas_type <- as.character.factor( curr_well$Type[1])
    meas_descr <- as.character.factor(curr_well$Description[1])
    meas_well <- as.character.factor(curr_well$Well[1])
    meas_num <- as.factor(1)
    
    lin_fit <- lm( abs1~time1min )   # poly3_fit <- lm( abs1~poly(time_delta,3) )
    
    curr_slope <-  coef(lin_fit)[['time1min']]
    curr_intercept <-  coef(lin_fit)[['(Intercept)']]

    tmp_ma[i,] <<- c( meas_well, barcode, meas_num, meas_type, meas_descr, curr_slope, curr_intercept)
    i <<- i + 1
  }
  
  invisible(by(kin_data_df, kin_data_df$Well, calc_lin_mod, wavelength))
  
  lm_df <- as.data.frame(tmp_ma)
  colnames(lm_df) <- col_names
  # out of a obscure reason, slope and intercept is converted to factor; now reverting:
  lm_df$Slope <- as.numeric.factor(lm_df$Slope)
  lm_df$Intercept <- as.numeric.factor(lm_df$Intercept)
  
  return(lm_df)
}

#' selectBestLinModel
#'
#' @title Select Best Linear Model for a given Data Frame
#' @description Calculates all possible linar models and stores coefficients in a data frame
#'      based on an idea of Martin Weiss
#' @param kin_data_df, wavelength
#' @keywords plate readers
#' @return data frame with 
#' @note relativly well runtime optimized version - don't be confused about the ugly code: it's quite fast
#' @export
#' @examples
#'  please wait until fixed !!!
#' @note todo: not yet adapted to new data frame structure !!
# 

selectBestLinModel <- function(kin_df)
{
  # definitions
  min_interval_size <- 20
  
  # determining the number of measurements from file
  num_meas_cycles <- #read.table(data_file_list[[1]], skip = num_cycles_row, nrows=1)[[2]]
  
  # converting kinetic data to 3D array for easier data handling
  all.data.arr <- array(unlist(absorptionsWells),c(8,12,num_meas_cycles))
  
  # functions
  
  analyze_per_well_kinetics <- function(kin_data.vec) {
    
    # calcualtes linear properties of one given datapoint interval
    calc_lin_properties <- function(first_data_point, last_data_point) {
      time_min <- all_times.vec[first_data_point:last_data_point]
      lin.mod <- lm(kin_data.vec[first_data_point:last_data_point] ~ time_min)
      
      return(c(r_squared=summary(lin.mod)$r.squared, lin_mod=lin.mod))
    }
    
    # iteration through all relevant right indices with minimal interval size of min_interval_size
    calc_all_lin_models <- function(first_data_point) {
      right.index.vec <- ((first_data_point+min_interval_size):num_meas_cycles)
      temp.lin.mod.list <- sapply(right.index.vec, function(last_data_point) calc_lin_properties(first_data_point, last_data_point) )
      local.max_r_sq <-which.max(temp.lin.mod.list[1,])
      
      return(temp.lin.mod.list[,local.max_r_sq])
    }
    
    # left index loop
    all.lin.coeff.list <- sapply((1:(num_meas_cycles - min_interval_size)), calc_all_lin_models)
    
    # selecting the global best r squared
    max_r_sq <-which.max(all.lin.coeff.list[1,])
    # selecting model with highest r squared
    best_lin_mod <- all.lin.coeff.list[,max_r_sq]
      
    return(best_lin_mod)
  }
  
  # main interation through all wells
  best_lin_mod_lst <- apply(all.data.arr, c(1,2), analyze_per_well_kinetics )

  #write.table(signif(slopes.mat, digits=4), file= csv_file_name, col.names = col.names, row.names=row.names, sep=",")
  
  return(best_lin_mod[[1]])
}

#' kinPlot
#'
#' @title Plotting Kinetic Absorption Data in Single files or Overview
#' @description 
#'   Slopes need to be pre-calculated to also plot max and min slopes
#' @param kin_abs_df (data frame) - all absorption data
#' @param barcode (string) 
#' @param wavelength (int)
#' @keywords plate readers
#' @export 
#' @examples
#'   system.time(kinPlot(kin_df, lin_mod_df, wavelength=245, markBest=TRUE))
#'   system.time(kinPlot(kin_df, lin_mod_df, wavelength=245, markBest=TRUE, singlePlot=T, overview=F))
#'    good parameters f. jpg: plotWidth=7600, plotHeight=4400, plotQuality=70
#'    single plot: plotWidth=1200, plotHeight=800, plotQuality=70
#' @note todo: >=384 well format plotting,  WT handling, new text positioning
#'  

kinPlot <- function(kin_abs_df, slopes_df, barcode="0000", 
                    wavelength=0, lineColor='red', overview=TRUE, singlePlot=FALSE, 
                    description=TRUE, markBest=FALSE,
                    plotWidth=7600, plotHeight=4400, plotQuality=70, filename = "_kinPlot", 
                    plotRef = FALSE, output_format='png' )
{
  xlim <- c(0,15.0)
  ylim <- c(0.0,3.1)
  plot_char <- 1
  num_col <- 10
  
  circle_colors <- colorRampPalette(c("blue","green","yellow","red"))(num_col+1) # rev(heat.colors(num_col))
  
  # select data of particular wavelength
  abs_wl_sel_df <- kin_abs_df[kin_abs_df$Wavelength == wavelength,]
  max_slope <- max(slopes_df$Slope)
  
  if (plotRef) {
    wt_df <- slopes_df[slopes_df$Type == 'R',]

    wt_wells <- wt_df$Well
    wt_slopes <- wt_df$Slope
    max_wt_slope <- max(wt_slopes)
    min_wt_slope <- min(wt_slopes)
  }
  
  # plot each single well panel
  wellPlot <- function(curr_well_df)
  {
    # *** praparation of plot data
    abs1 <- curr_well_df$Value
    time1 <- curr_well_df$Time
    time1min <- time1/60
  
    curr_well <- as.character.factor(curr_well_df$Well[1])

    #transfroming seconds to minutes
    time1min <- time1/60

    
    curr_slope_df <- slopes_df[slopes_df$Well == curr_well,]
    
    curr_slope <- curr_slope_df$Slope
    curr_intercept <- curr_slope_df$Intercept
    meas_type <- curr_slope_df$Type
    meas_descr <- curr_slope_df$Description
    
    # *** preparation of plot
    if(singlePlot) {
      switch(output_format,
             jpeg={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".jpg", sep="" )
                    jpeg(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
             png={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".png", sep="" )
                   png(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, res=120) },
             svg={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".svg", sep="" )
                   svg(curr_plot_filename, antialias="default",width=3000, height=1000) },
             { cat(output_format, "- unknown output format specified") }
      )
    }
    
    # * plotting raw data points 
    plot(abs1~time1min, pch = plot_char, ann=FALSE,  type="b", xlim=xlim, ylim=ylim,
         xlab="time / min", ylab="abs / mAU")
    
    abline( curr_intercept, curr_slope , col=lineColor, lwd = 3.0)

    ## plotting min and max reference slope
    if(plotRef) {
      max_wt_slope_line <- c(curr_intercept, max(wt_slopes))
      min_wt_slope_line <- c(curr_intercept, min(wt_slopes))
      abline( max_wt_slope_line, col='pink', lty=2 )
      abline( min_wt_slope_line, col='pink', lty=2 )
      if (curr_well %in% wt_wells) box( lwd=4.0) # mark reference wells
    }
    
    x_intv = xlim[2]-xlim[1]
    y_intv = ylim[2]-ylim[1]
        
    # * plotting boxes
    if(markBest) {
      slope_col <- circle_colors[curr_slope/max_slope*10+1]
      symbols(x_intv * 0.3, y_intv * 0.93, circles=c(0.8), bg=slope_col,
              inches=FALSE, add=T)
      box(col=slope_col, lwd=4.0)  
      if (curr_slope  >= max_slope) box(col="red", lwd=10.0)
    }

    # * adding info into the graph (well number, slope, description)    
    
    text(x_intv * 0.1, y_intv * 0.93, curr_well, cex= 2 ) 
    if(description) text(x_intv * 0.12, y_intv * 0.86, paste(meas_type, " : ",  meas_descr, sep=" "), cex= 0.8 ) 
   
    text(x_intv * 0.15, y_intv * 0.05, 
         paste("slope =", signif(curr_slope, digits=3)  , "AU/min" ,  sep = " "), col='darkred')
    
    grid(col='gray')
    # * close output file  
    if(singlePlot) dev.off()
  }
  
  # **** plotting all data
  if (overview)
  {
    switch(output_format,
           jpeg={ overview_file_name <- paste(barcode, filename, "_plateView.jpg", sep="" )
                  jpeg(overview_file_name,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
           png={ overview_file_name <- paste(barcode, filename, "_plateView.png", sep="" )
                 png(overview_file_name,  units="px", width=plotWidth, height=plotHeight, res=120) },
           svg={ overview_file_name <- paste(barcode, filename, "_plateView.svg", sep="" )
                 svg(overview_file_name, antialias="default",width=3000, height=1000) },
          { cat(output_format, "- unknown output format specified") }
    )
    par(mfrow=c(8,12))
  }
  
  invisible( by(abs_wl_sel_df, abs_wl_sel_df$Well, wellPlot) )

  if(overview) dev.off()
}

#' kinPlotMP
#'
#' @title Plotting Kinetic Data with Multiple Parameters (growth, activity, fluorescense, ratio act/fl)
#' @description 
#'   Slopes need to be pre-calculated to also plot max and min slopes
#' @param   kin_abs_df (data frame)
#' @param   slopes_df (data frame)
#' @param   fl_df (data frame)
#' @keywords plate readers
#' @export 
#' @examples
#'   system.time(kinPlotMP(kin_df, lin_mod_df, wavelength=245, markBest=TRUE))
#'    good parameters f. jpg: plotWidth=7600, plotHeight=4400, plotQuality=70
#'    single plot: plotWidth=1200, plotHeight=800, plotQuality=70
#' @note todo:  circles for high fl or high slope
#'  

kinPlotMP <- function(kin_abs_df, slopes_df, fl_df, barcode="0000", 
                      threshold = 1.0, wavelength=0, overview=TRUE, singlePlot=FALSE, 
                      description=TRUE, markBest=FALSE,
                      plotWidth=7600, plotHeight=4400, plotQuality=70, filename = "_kinPlotMP", 
                      plotRef = FALSE, lineColor='red', output_format='png' )
{
  xlim <- c(0,15.0)
  ylim <- c(0.0,3.1)
  plot_char <- 1
  
  # select data of particular wavelength
  abs_wl_sel_df <- kin_abs_df[kin_abs_df$Wavelength == wavelength,]
  
  wt_fl_df <- fl_df[fl_df$Type == 'R',]
  
  #wt_wells <- wt_fl_df$Well
  wt_fl = wt_fl_df$Value
  max_wt_fl <- max(wt_fl, rm.na = TRUE)

  max_slope <- max(slopes_df$Slope)
  wt_slopes_df <- slopes_df[slopes_df$Type == 'R',]$Slope
  wt_slopes <- wt_slopes_df$Slope
  max_wt_slope <- max(wt_slopes)
  min_wt_slope <- min(wt_slopes)
  av_wt_slope <- mean(wt_slopes)
  
  wt_wells <- wt_slopes_df$Well

  wt_ratios <- wt_slopes / wt_fl
  
  max_sl_fl_ratio = max(wt_ratios)
  
  # plot each single well panel
  wellPlot <- function(curr_well_df)
  {
    # *** praparation of plot data
    abs1 <- curr_well_df$Value
    time1 <- curr_well_df$Time
    time1min <- time1/60
    
    curr_well <- as.character.factor(curr_well_df$Well[1])
    
    #transfroming seconds to minutes
    time1min <- time1/60
    
    curr_slope_df <- slopes_df[slopes_df$Well == curr_well,]
    
    curr_slope <- curr_slope_df$Slope
    curr_intercept <- curr_slope_df$Intercept
    meas_type <- curr_slope_df$Type
    meas_descr <- curr_slope_df$Description
            
    curr_fl <- fl_df[(fl_df$Well == curr_well),]$Value
    
    curr_act_fl_ratio <- curr_slope / curr_fl
    
    if(is.na(curr_fl) ) curr_fl = 0.0
        
    # *** preparation of plot
    if(singlePlot) {
      switch(output_format,
            jpeg={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".jpg", sep="" )
                   jpeg(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
            png={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".jpg", sep="" )
                  png(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, res=120) },
            svg={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".jpg", sep="" )
                  svg(curr_plot_filename, antialias="default",width=3000, height=1000) },
            { cat(output_format, "- unknown output format specified") }
      )
    }

    # * plotting raw data points 
    plot(abs1~time1min, pch = plot_char, ann=FALSE,  type="b", xlim=xlim, ylim=ylim,
         xlab="time / min", ylab="abs / mAU")
    
    abline( curr_intercept, curr_slope , col=lineColor, lwd = 3.0)
        
    # plotting min and max wt slope
    if(plotRef) {
      max_wt_slope_line <- c(curr_intercept, max(wt_slopes))
      min_wt_slope_line <- c(curr_intercept, min(wt_slopes))
      abline( max_wt_slope_line, col='pink', lty=2)
      abline( min_wt_slope_line, col='pink', lty=2)
      if (curr_well %in% wt_wells) box( lwd=4.0) # mark reference wells
    }
    
    # * plotting boxes
    #if (curr_act_fl_ratio  > ( wt_act_fl_max_ratio * improvement_factor) )    box(col="red", lwd=10.0)
    if(markBest) if (curr_act_fl_ratio > max_sl_fl_ratio  * threshold ) box(col="red", lwd=10.0)
    
    grid(col='gray')
    axis(side = 2)
    
    # Fluorescent bar plotting
    par(new = TRUE)
    barplot(height=c(0,0,0,0,0,curr_fl), col = "green", axes = FALSE, xlim = c(0,7), ylim=c(0.0,20.0))

    #mtext(side = 4, line = 3, "FL", cex=0.8, adj=1, padj=1)
    # * adding text at top of bars
    text(x = 6.7, y = curr_fl, label = curr_fl , pos = 3, cex = 0.9, col = "darkgreen")
    axis(side = 4)

    # * adding info into the graph (well number, slope, description, best fl, best slope), 
    # * with new coord. system
    par(new = T)
    plot(0.0,0.0, xlim=c(0.0,1.0), ylim=c(0.0,1.0), axes=F, col='white'  ) # dummy plot to get rid of axes 
    text(0.1, 0.93, curr_well, cex= 2 ) 
    if(description) text(0.12, 0.86, paste(meas_type, " : ",  meas_descr, sep=" "), cex= 0.6 ) 
    
    if (curr_fl  > max_wt_fl) symbols(0.23,0.93, circles=c(0.04),fg='darkgreen', bg='green', inches=FALSE, add=T)
    if (curr_slope  > max_wt_slope) symbols(0.32,0.93, circles=c(0.04),fg='darkred', bg='red', inches=FALSE, add=T)
    if (curr_act_fl_ratio  > max_sl_fl_ratio ) {
           symbols(0.42,0.93, circles=c(0.04),fg='darkblue', bg='blue', inches=FALSE, add=T)
           # add text with % comp. to WT
    }
    
    text(0.135, 0.05, col="darkred", paste("slope =", signif(curr_slope, digits=3), "AU/min" ,  sep = " "))
    text(0.14, 0.01, col="darkblue", paste("ratio: slope/fl =", signif(curr_act_fl_ratio, digits=3),  sep = " "))
    
    # * close output file  
    if(singlePlot) dev.off()
  }
  
  # **** plotting all data
  if (overview)
  {
    switch(output_format,
          jpeg={ overview_file_name <- paste(barcode, filename, "_plateView.jpg", sep="" )
                 jpeg(overview_file_name,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
          png={ overview_file_name <- paste(barcode, filename, "_plateView.png", sep="" )
                png(overview_file_name,  units="px", width=plotWidth, height=plotHeight, res=120) },
          svg={ overview_file_name <- paste(barcode, filename, "_plateView.svg", sep="" )
                svg(overview_file_name, antialias="default",width=3000, height=1000) },
          { cat(output_format, "- unknown output format specified") }
    )
    par(mfrow=c(8,12))  # plot layout: 8x12 panels
  }
  
  invisible( by(abs_wl_sel_df, abs_wl_sel_df$Well, wellPlot) )
  
  if(overview) dev.off()
}


#' barPlotMP
#'
#' @title Plotting kinetic data with Multiple Parameters with 2D Barplots
#' @description 
#'   Slopes need to be pre-calculated to also plot max and min slopes
#' @param filename
#' @keywords plate readers
#' @export 
#' @examples
#'   system.time(kinPlot(kin_df, lin_mod_df, wavelength=245, markBest=TRUE))
#'    good parameters f. jpg: plotWidth=7600, plotHeight=4400, plotQuality=70
#'    single plot: plotWidth=1200, plotHeight=800, plotQuality=70
#' @note todo:  circles for high fl or high slope, still very ugly 
#'  

barPlotMP <- function(kin_abs_df, slopes_df, fl_df, growth_df, barcode="0000", 
                      wavelength=0, lineColor='red', overview=TRUE, singlePlot=FALSE, 
                      description=TRUE, markBest=FALSE,
                      plotWidth=7600, plotHeight=4400, plotQuality=70, filename = "_barPlotMP", 
                      plotRef = FALSE, output_format='jpeg' )
{
  xlim <- c(0,15.0)
  ylim <- c(0.0,3.1)
  plot_char <- 1
  
  temp_growth_df <- growth_df[ growth_df$Num == max(levels(growth_df$Num)), ]
  # select data of particular wavelength
  abs_wl_sel_df <- kin_abs_df[kin_abs_df$Wavelength == wavelength,]
  max_slope <- max(slopes_df$Slope)
  
  wt_fl = fl_df[fl_df$Type == 'R',]$Value
  max_wt_fl <- max(wt_fl, rm.na = TRUE)
  
  # !!! WT slope !
  if (plotRef) {
    wt_slopes <- slopes_df[slopes_df$Type == 'R',]$Slope
    max_wt_slope <- max(wt_slopes)
    min_wt_slope <- min(wt_slopes)
  }
  
  # plot each single well panel
  wellPlot <- function(curr_well_df)
  {
    # *** praparation of plot data
    abs1 <- curr_well_df$Value
    time1 <- curr_well_df$Time
    time1min <- time1/60
    
    curr_well <- as.character.factor(curr_well_df$Well[1])
    
    #transfroming seconds to minutes
    time1min <- time1/60

    curr_growth <- temp_growth_df[(temp_growth_df$Well == curr_well),]$Value
    
    curr_slope_df <- slopes_df[slopes_df$Well == curr_well,]
    
    curr_slope <- curr_slope_df$Slope
    curr_intercept <- curr_slope_df$Intercept
    meas_type <- curr_slope_df$Type
    meas_descr <- curr_slope_df$Description
    
    max_wt_slope_line <- c(curr_intercept, max_wt_slope)
    min_wt_slope_line <- c(curr_intercept, min_wt_slope)
    
    curr_fl <- fl_df[(fl_df$Well == curr_well),]$Value
    
    curr_act_fl_ratio <- curr_slope / curr_fl
    
    if(is.na(curr_fl) ) curr_fl = 0.0
    
    #if (curr_fl > fl_threshold) curr_act_fl_ratio <-  curr_slope / curr_fl[1]
    #else curr_act_fl_ratio <- 0.0
    
    # *** preparation of plot
    if(singlePlot) {
      switch(output_format,
             jpeg={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".jpg", sep="" )
                    jpeg(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
             png={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".png", sep="" )
                   png(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, res=120) },
             svg={ curr_plot_filename <- paste(barcode,'_', curr_well, filename,".svg", sep="" )
                   svg(curr_plot_filename, antialias="default",width=3000, height=1000) },
             { cat(output_format, "- unknown output format specified") }
      )
    }

    barplot(c(curr_growth * 1), col = "orange",  axes = TRUE,
              xlim = c(0.0,5.0), ylim=c(0.0,7.0))
    text(x = 1.0 , y = curr_growth, label = curr_growth , pos = 3, cex = 0.9, col = "orange")
    grid(col='gray')
    axis(side = 2)

    par(new = TRUE)
      barplot(c(0,curr_slope *1), col = "red",  axes = F, xlab = NA, ylab = NA, 
              xlim = c(0.0,5.0), ylim=c(0.0, 0.8))
    text(x = 2.0 , y = curr_slope, label = curr_slope , pos = 3, cex = 0.9, col = "darkred")
      #axis(side = 4)

    par(new = TRUE)
      barplot(height=c(0,0,curr_fl * 1 ), col = "green", axes = FALSE, xlim = c(0.0,5.0), ylim=c(0.0,40.0))
      text(x = 3.0 , y = curr_fl, label = curr_fl , pos = 3, cex = 0.9, col = "darkgreen")

    par(new = TRUE)
      barplot(c(0,0,0,curr_act_fl_ratio * 1), col = "blue",  axes = F, xlab = NA, ylab = NA, 
               xlim = c(0.0,5.0), ylim=c(0.0,0.01))
    text(x = 4.0 , y = curr_act_fl_ratio, label = curr_act_fl_ratio , pos = 3, cex = 0.9, col = "darkblue")

#    abline( curr_intercept, curr_slope , col=lineColor, lwd = 3.0)

    #mtext(side = 4, line = 3, "FL", cex=0.8, adj=1, padj=1)

    # * plotting boxes
    #if (curr_act_fl_ratio  > ( wt_act_fl_max_ratio * improvement_factor) )    box(col="red", lwd=10.0)
    if(markBest) if (curr_slope  >= max_slope) box(col="red", lwd=10.0)

    # * adding info into the graph (well number, slope, description, best fl, best slope), 
    # * with new coord. system
    par(new = T)
    plot(0.0,0.0, xlim=c(0.0,1.0), ylim=c(0.0,1.0), axes=F, col='white'  ) # dummy plot to get rid of axes 
    if (curr_fl  >= max_wt_fl) symbols(0.23,0.93, circles=c(0.04),fg='darkgreen', bg='green', inches=FALSE, add=T)
    if (curr_slope  >= max_slope) symbols(0.32,0.93, circles=c(0.04),fg='darkred', bg='red', inches=FALSE, add=T)
    text(0.1, 0.93, curr_well, cex= 2 ) 
    
    if(description) text(0.12, 0.86, paste(meas_type, " : ",  meas_descr, sep=" "), cex= 0.6 ) 
    
    text(0.13, 0.80, paste("slope =", signif(curr_slope, digits=3), "AU/min" ,  sep = " "), cex= 0.6)
    text(0.13, 0.76, paste("ratio: slope/fl =", signif(curr_act_fl_ratio, digits=3),  sep = " "), cex= 0.6 )
    
    
    # * close output file  
    if(singlePlot) dev.off()
  }
  
  # **** plotting all data
  if (overview)
  {
    switch(output_format,
           jpeg={ overview_file_name <- paste(barcode, filename, "_plateView.jpg", sep="" )
                  jpeg(overview_file_name,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
           png={ overview_file_name <- paste(barcode, filename, "_plateView.png", sep="" )
                 png(overview_file_name,  units="px", width=plotWidth, height=plotHeight, res=120) },
           svg={ overview_file_name <- paste(barcode, filename, "_plateView.svg", sep="" )
                 svg(overview_file_name, antialias="default",width=3000, height=1000) },
          { cat(output_format, "- unknown output format specified") }
    )
    par(mfrow=c(8,12))
  }

  invisible( by(abs_wl_sel_df, abs_wl_sel_df$Well, wellPlot) )

  if(overview) dev.off()
}

#' boxPlotMP
#'
#' @title Plotting kinetic data with Multiple Parameters in one single boxplot
#' @description 
#'   Slopes need to be pre-calculated to also plot max and min slopes
#' @param filename
#' @keywords plate readers
#' @export 
#' @examples
#'   system.time(kinPlot(kin_df, lin_mod_df, wavelength=245, markBest=TRUE))
#'    good parameters f. jpg: plotWidth=7600, plotHeight=4400, plotQuality=70
#'    single plot: plotWidth=1200, plotHeight=800, plotQuality=70
#' @note todo:  not yet finished - very very ugly
#'  

boxPlotMP <- function(kin_abs_df, slopes_df, fl_df, growth_df, barcode="0000", 
                      wavelength=0, lineColor='red',
                      plotWidth=7600, plotHeight=4400, plotQuality=70, filename = "_boxPlotMP", 
                      output_format='jpeg' )
{
  xlim <- c(0,15.0)
  ylim <- c(0.0,3.1)
  plot_char <- 1
  
  temp_growth_df <- growth_df[ growth_df$Num == max(levels(growth_df$Num)), ]
  # select data of particular wavelength
  abs_wl_sel_df <- kin_abs_df[kin_abs_df$Wavelength == wavelength,]
  max_slope <- max(slopes_df$Slope)
  
  wt_fl = fl_df[fl_df$Type == 'R',]$Value
  max_wt_fl <- max(wt_fl, rm.na = TRUE)
  
  # !!! WT slope !
    wt_slopes <- slopes_df[slopes_df$Type == 'R',]$Slope
    max_wt_slope <- max(wt_slopes)
    min_wt_slope <- min(wt_slopes)
  
  norm_growth <- cbind( value=growth_data[[1]]$Value/growth_av, pos1=1.0)
  norm_growth[norm_growth[,'value'] < 0.1] = NA
  norm_growth_df <- as.data.frame(norm_growth)
  boxplot(formula=value~pos1, data=norm_growth_df, at=(1.0), col='orange', ylim=c(0,1.4),xlim=c(0,5.0),  outline=FALSE)
  par(new=T)
  norm_fl <- cbind( value=fl_data_df$Value/fl_av, pos2=2.0)
  norm_fl[norm_fl[,'value'] < 0.1] = NA
  norm_fl_df <- as.data.frame(norm_fl)
  boxplot(formula=value ~ pos2, data=norm_fl_df, at=c(2.0), col='green',  ylim=c(0,1.4),xlim=c(0,5.0),  outline=F)
  
  par(new=T)
  norm_slope <- cbind( value=slope_data/slope_av, pos3=3.0)
  norm_slope[norm_slope[,'value'] < 0.1] = NA
  norm_slope_df <- as.data.frame(norm_slope)
  boxplot(formula=value ~ pos3, data=norm_slope_df, at=c(3.0), col='red',  ylim=c(0,1.4),xlim=c(0,5.0),  outline=F)
  
  par(new=T)
  norm_ratio <- cbind( value=norm_slope_df[,'value']/norm_fl_df[,'value'], pos4=4.0)
  norm_ratio[norm_ratio[,'value'] < 0.1] = NA
  norm_ratio_df <- as.data.frame(norm_ratio)
  boxplot(formula=value ~ pos4, data=norm_ratio_df, at=c(4.0), col='blue',  ylim=c(0,1.4),xlim=c(0,5.0),  outline=F)
  
  grid(nx=2,col='gray')
  
# **** plotting all data

  switch(output_format,
         jpeg={ overview_file_name <- paste(barcode, filename, "_plateView.jpg", sep="" )
                jpeg(overview_file_name,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
         png={ overview_file_name <- paste(barcode, filename, "_plateView.png", sep="" )
               png(overview_file_name,  units="px", width=plotWidth, height=plotHeight, res=120) },
         svg={ overview_file_name <- paste(barcode, filename, "_plateView.svg", sep="" )
               svg(overview_file_name, antialias="default",width=3000, height=1000) },
         { cat(output_format, "- unknown output format specified") }
  )
  dev.off()
}
