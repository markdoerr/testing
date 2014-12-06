
plotPlateOverview <- function(curr_well, curr_wl)
{
  curr_graph_file_name <- paste(graph_file_name_jpeg, curr_well, ".jpg", sep="" )
  
  abs1 <- abs_data_lst[(abs_data_lst$WL == curr_wl & abs_data_lst$Well == curr_well),]$Value
  time1 <- abs_data_lst[(abs_data_lst$WL == curr_wl & abs_data_lst$Well == curr_well),]$Time
  
  #transfroming seconds to minutes
  time1min <- time1/60
  
  curr_slope <- lin_mod_df[,curr_well]$Slope
  curr_intercept <- lin_mod_df[,curr_well]$LinMod.coefficients[1]
  
  max_wt_slope_line <- c(curr_intercept, max(wt_slopes))
  min_wt_slope_line <- c(curr_intercept, min(wt_slopes))
  
  curr_fl <- fl_data_df[(fl_data_df$Well == curr_well),]$Value
  
  gd <- growth_data[[1]]
  curr_growth <- gd[(gd$Well == curr_well),]$Value
  
  curr_slope_line_norm <- c(curr_intercept, curr_slope/curr_fl[1])
  max_wt_slope_line_norm <- c(curr_intercept, max(wt_slopes/curr_fl[1]))
  min_wt_slope_line_norm <- c(curr_intercept, min(wt_slopes/curr_fl[1]))
  
  if (curr_fl[1] > fl_threshold) curr_act_fl_ratio <-  curr_slope / curr_fl[1]
  else curr_act_fl_ratio <- 0.0
  
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
  
  #barplot(c(0,curr_fl[1]/fl_av), col = "green",  axes = T, xlab = NA, ylab = NA, 
  #        xlim = c(0.0,5.0), ylim=c(0.0,2.0))
  #text(x = 2.0, y = curr_fl[1]/fl_av, label = "fl" , pos = 3, cex = 2, col = "darkgreen")
  
  
  #par(new = T)
  #barplot(c(curr_growth / growth_av), col = "orange",  axes = F, xlab = NA, ylab = NA, 
  #          xlim = c(0.0,5.0), ylim=c(0.0,2.0))
  #text(x = 0.9, y = curr_growth / growth_av, label = "gr" , pos = 3, cex = 2, col = "orange")
  #abline(1.0,0, col="red" )
  #par(new = T)
  #barplot(c(0,0,curr_slope /slope_av), col = "red",  axes = F, xlab = NA, ylab = NA, 
  #                  xlim = c(0.0,5.0), ylim=c(0.0,2.0))
  #text(x = 3.0, y = curr_slope /slope_av, label = "sl" , pos = 3, cex = 2, col = "red")
  
  #par(new = T)
  #barplot(c(0,0,0,curr_act_fl_ratio /ratio_av), col = "blue",  axes = F, xlab = NA, ylab = NA, 
  #          xlim = c(0.0,5.0), ylim=c(0.0,2.0))
  #text(x = 4.05, y = curr_act_fl_ratio /ratio_av, label = "ratio" , pos = 3, cex = 2, col = "blue")
  
  grid()
  
  ##jpeg(curr_graph_file_name,  units="px", width=1200, height=1024, quality=100)
  ## plotting raw data points
  #plot(abs1~time1min, pch = plot_char, ann=FALSE,  type="b", xlim=xlim, ylim=ylim,
  #     xlab="time / min", ylab="abs / mAU")
  
  ##if (curr_act_fl_ratio > wt_act_fl_ratio )    box(col="red", lwd=6.0)
  
  #if (curr_act_fl_ratio  > ( wt_act_fl_max_ratio * improvement_factor) )    box(col="red", lwd=10.0)
  ##if (curr_slope  > (wt_slopes_av * 1.0)) box(col="red", lwd=10.0)
  
  #if (curr_fl[1] > wt_fl_max )    rect(xlim[2]*0.030,ylim[2]*0.85,xlim[2]*0.18,ylim[2]*0.97, border="red", lwd=10.0)
  
  ## adding well number info into the graph
  text(xlim[2]-xlim[2]*0.9,ylim[2]-ylim[2]*0.09, paste(curr_well ,  sep = " "), cex= 2 ) #add=TRUE
  text(xlim[2]-xlim[2]*0.87,ylim[2]-ylim[2]*0.25, 
       paste("slope =", signif(curr_slope, digits=3)  , "AU/min" ,  sep = " "))
  text(xlim[2]-xlim[2]*0.89,ylim[2]-ylim[2]*0.28, 
       paste("ratio =", signif(curr_act_fl_ratio, digits=3)  , "rel" ,  sep = " "))
  
  #abline( lin_mod_df[,curr_well]$LinMod.coefficients, col="red")
  #abline( max_wt_slope_line, col='pink')
  #abline( min_wt_slope_line, col='pink')
  
  ##abline( curr_slope_line_norm, col='darkgreen')
  ##abline( max_wt_slope_line_norm, col='lightgreen')
  ##abline( min_wt_slope_line_norm, col='lightgreen')
  
  # Fluorescent bar plotting
  #par(new = T)
  
  # # Add text at top of bars
  #  text(x = 9.05, y = curr_fl[1], label = curr_fl[1] , pos = 3, cex = 0.9, col = "darkgreen")
  #axis(side = 4)
  #mtext(side = 4, line = 3, "FL")
  #  par(new = T)
  #  barplot(c(0,0,0,0,0,0,curr_slope *100,0), col = "red",  axes = F, xlab = NA, ylab = NA, 
  #          xlim = c(0.0,10.0), ylim=c(0.0,10.0))
  #  par(new = T)
  #  barplot(c(0,0,0,0,0,0,0,curr_act_fl_ratio * 3000,0), col = "blue",  axes = F, xlab = NA, ylab = NA, 
  #          xlim = c(0.0,10.0), ylim=c(0.0,10.0))
  #  par(new = T)
  #  barplot(c(0,0,0,0,curr_growth * 10), col = "orange",  axes = F, xlab = NA, ylab = NA, 
  #          xlim = c(0.0,10.0), ylim=c(0.0,10.0))
  
  #lines(time_delta, predict(poly3_fit, data.frame(x=time_delta)), col='red')
  #print(summary(poly3_fit))
  #dev.off()
}