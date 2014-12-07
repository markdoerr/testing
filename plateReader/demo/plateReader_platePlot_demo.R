
#' 
#' @title plateReader and platePlot demo
#' @description 
#'   change working directory to plateReader/demo
#'   run each line individually to see, how things work ....
#'   enjoy :)  
#'   
#' @author "mark.doerr <mark.doerr@uni-greifswald.de> [aut, cre]"

library("rgl")
library("plateReader")
library("platePlot")

# loading bacterial growth data from multiple data files with file pattern _OD600_
growth_df <- importReaderData("_OD660_", method='SPabsMatr', layout=F)

# show barplot, wavelength is important for files with multiple wavelengths !
platePlot3d(growth_df,  wavelength=660, scale=1.5)

#2D average growth plot
growth_pl_df <- addPlateLayout(growth_df)
growthPlot(growth_pl_df)

# growth-expression plot with pathlength correction (PLC)
growth_df <- importReaderData("_gr.DAT", method='SPabsMatr', PLC=TRUE)
expr_df <- importReaderData("_expr_", method='SPabsMatr', PLC=TRUE)

# growth only
growthExpressionPlot(growth_df)

# expression only
growthExpressionPlot(growth_df=NULL, expr_df=expr_df)

# plot growth and expression
growthExpressionPlot(growth_df, expr_df)

# loading fluorescence data
fl_df <- importReaderData("_SPfl_", method="SPfl", device='varioskan')

# plot fluorescence data
platePlot3d(fl_df, column_colors ='green', scale=0.1)

# loading kinetic data from single file
kin_df <- importReaderData("_245_265_", method="KINabs", device='varioskan', PLC=TRUE)

# calc allo activity slopes
slopes_df <- calcAllLinModels(kin_df, wavelength=245)

# plotting 2D overview plot in jpeg file
kinPlot(kin_df, slopes_df, wavelength=245, markBest=TRUE, plotRef=TRUE,
        plotWidth=7600, plotHeight=4400, plotQuality=70,  output_format='png' )

# plotting 2D plots in mulitple files
kinPlot(kin_df, slopes_df, wavelength=245, overview=FALSE, singlePlot=TRUE, markBest=TRUE, plotRef=TRUE,
        plotWidth=1200, plotHeight=1024, plotQuality=70, output_format='png')

# plot fluorescence data
platePlot3d(slopes_df, column_colors ='red', use_slope = TRUE, scale=20)

# *******************  FIN  ********************

