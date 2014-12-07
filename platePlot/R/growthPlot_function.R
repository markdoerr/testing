#' growthPlot
#'
#' @title Plotting Bacterial Growth Data
#' @description 
#'   Slopes need to be pre-calculated to also plot max and min slopes
#' @param filename
#' @keywords plate readers
#' @export 
#' @examples
#'    good parameters f. jpg: plotWidth=7600, plotHeight=4400, plotQuality=70
#'    single plot: plotWidth=1200, plotHeight=800, plotQuality=70
#' @note todo: >=384 well format plotting,  WT handling, new text positioning
#' 

growthPlot  <- function(growth_df, wavelength=660, lineColor='red',
                        plotTitle = "Average Growth of Plate ",
                        plotWidth=1200, plotHeight=1024, plotQuality=70, 
                        filename = "growthPlot", output_format='png' )
{
  library(gplots)
  
  growth_sel_df <- growth_df[(growth_df$Wavelength == wavelength & growth_df$Type == 'S'),]

  barcode <-  growth_sel_df$Barcode[1] 
  date_time_ref = min(growth_sel_df$DateTime)
  if(plotTitle != "") plotTitle <-  paste(plotTitle, barcode, " (", wavelength, "nm)", sep="" )
  
  plot_df <- NULL
  calcAverageGrowth <- function(meas_df)
  {    
    mean_abs <- mean(meas_df$Value);     
    sd_abs <- sd(meas_df$Value);     
    time_diff <-  difftime(meas_df$DateTime, date_time_ref , units="mins"); 
    
    plot_df <<- rbind(plot_df, data.frame('MeanAbs' = mean_abs, 'TimeDiff'= time_diff[1], 'Sd'=sd_abs)) 
  }
  
  by(growth_sel_df, growth_sel_df$Num, calcAverageGrowth )
  
  switch(output_format,
         jpeg={ curr_plot_filename <- paste(barcode,'_', filename,".jpg", sep="" )
                jpeg(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
         png={ curr_plot_filename <- paste(barcode,'_', filename,".png", sep="" )
               png(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, res=120) },
         svg={ curr_plot_filename <- paste(barcode,'_', filename,".svg", sep="" )
               svg(curr_plot_filename, antialias="default",width=3000, height=1000) },
         { cat(output_format, "- unknown output format specified") }
  )

# workaround without gplots:
#plot( plot_df$MeanAbs ~ plot_df$TimeDiff, type = "b" , main = plotTitle, xlab = "time [min]", ylab = "Absorption [AU]" )
#arrows(plot_df$TimeDiff, plot_df$MeanAbs-plot_df$Sd, plot_df$TimeDiff, plot_df$MeanAbs+plot_df$Sd, length=0.08, angle=90, code=3)

plotCI(plot_df$TimeDiff, plot_df$MeanAbs, uiw = plot_df$Sd, type = "b", 
       main = plotTitle, xlab = "time [min]", ylab = "Absorption [AU]" )

dev.off()
}

#' growthExpressionPlot
#'
#' @title Plotting bacterial growth and Expression Data
#' @description 
#'   Slopes need to be pre-calculated to also plot max and min slopes
#' @param filename
#' @keywords plate readers
#' @export 
#' @examples
#'    good parameters f. jpg: plotWidth=7600, plotHeight=4400, plotQuality=70
#'    single plot: plotWidth=1200, plotHeight=800, plotQuality=70
#' @note todo: connection line growth expression
#' 

growthExpressionPlot  <- function(growth_df=NULL, expr_df=NULL, wavelength=660, growthColor='darkgreen', exprColor='red',
                        plotTitle = "Av. Growth and Expression of Plate ",
                        plotWidth=1200, plotHeight=1024, plotQuality=70, 
                        filename = "growthExprPlot", output_format='png' )
{
  library(gplots)
  
  growth_sel_df <- growth_df[(growth_df$Wavelength == wavelength & growth_df$Type == 'S'),]
  expr_sel_df <- expr_df[(expr_df$Wavelength == wavelength & expr_df$Type == 'S'),]
    
  plot_df <- NULL
  calcAverageGrowth <- function(meas_df)
  {    
    mean_abs <- mean(meas_df$Value);     
    sd_abs <- sd(meas_df$Value);     
    time_diff <-  difftime(meas_df$DateTime, date_time_ref , units="mins"); 
    
    plot_df <<- rbind(plot_df, data.frame('MeanAbs' = mean_abs, 'TimeDiff'= time_diff[1], 'Sd'=sd_abs)) 
  }
  
  if( ! is.null(growth_sel_df)) {
    barcode <-  growth_sel_df$Barcode[1] 
    date_time_ref = min(growth_sel_df$DateTime)
    by(growth_sel_df, growth_sel_df$Num, calcAverageGrowth )
  }
  else {
    if( ! is.null(expr_sel_df)) {
      barcode <-  expr_sel_df$Barcode[1] 
      date_time_ref = min(expr_sel_df$DateTime)
    }
    else print("ERROR (growthExpressionPlot): no plottable data available !!")
  }
  
  plot_growth_df <- plot_df
  #print(plot_df)
  plot_df <- NULL # as.data.frame( plot_df[nrow(plot_df),])  # resetting dataframe

  if( ! is.null(expr_df)) by(expr_sel_df, expr_sel_df$Num, calcAverageGrowth )
  
  plot_expr_df <- plot_df
  # adding first data point of expression to last data point of growth to combine the two plots
  if( ! is.null(plot_expr_df)) {
    plot_growth_df <- rbind(plot_growth_df, plot_expr_df[1,])
    xlim = c(0.0, max(plot_expr_df$TimeDiff) * 1.05 )
    ylim = c(0.0, max(plot_expr_df$MeanAbs) * 1.3 )
  }
  else {
    xlim = c(0.0, max(plot_growth_df$TimeDiff) * 1.05 )
    ylim = c(0.0, max(plot_growth_df$MeanAbs) * 1.3 )
  }
  
  switch(output_format,
         jpeg={ curr_plot_filename <- paste(barcode,'_', filename,".jpg", sep="" )
                jpeg(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, quality=plotQuality, res=120) },
         png={ curr_plot_filename <- paste(barcode,'_', filename,".png", sep="" )
               png(curr_plot_filename,  units="px", width=plotWidth, height=plotHeight, res=120) },
         svg={ curr_plot_filename <- paste(barcode,'_', filename,".svg", sep="" )
               svg(curr_plot_filename, antialias="default",width=3000, height=1000) },
         { cat(output_format, "- unknown output format specified") }
  )

  if(plotTitle != "") plotTitle <-  paste(plotTitle, barcode, " (", wavelength, "nm)", sep="" )
  
# workaround without gplots:
#plot( plot_df$MeanAbs ~ plot_df$TimeDiff, type = "b" , main = plotTitle, xlab = "time [min]", ylab = "Absorption [AU]" )
#arrows(plot_df$TimeDiff, plot_df$MeanAbs-plot_df$Sd, plot_df$TimeDiff, plot_df$MeanAbs+plot_df$Sd, length=0.08, angle=90, code=3)

  if( ! is.null(plot_growth_df)) {
    plotCI(plot_growth_df$TimeDiff, plot_growth_df$MeanAbs, uiw = plot_growth_df$Sd, type = "b", col=growthColor,
           main = plotTitle, xlab = "time [min]", ylab = "Absorption [AU]" , xlim=xlim, ylim=ylim )
    par(new=TRUE)
  }
  if( ! is.null(plot_expr_df))
    plotCI(plot_expr_df$TimeDiff, plot_expr_df$MeanAbs, uiw = plot_expr_df$Sd, type = "b", col=exprColor, 
           xlim=xlim, ylim=ylim, xlab = "", ylab="")

  dev.off()
}


#  growthPlotPredict
#  plot with growth prediction


