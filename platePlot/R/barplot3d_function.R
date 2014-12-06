
#' cubeFactory
#'
#' @title Plotting single cubes
#' @param cube_vec, cube_width, column_colors, num_colors=20
#' @keywords plots for microtiter plates
#' @export 
#' @examples
#' importReaderData()
#' 
#' @note todo: nicer and faster
#' 

cubeFactory <-function(cube_vec, cube_width, column_colors, num_colors=20)
{  
  # geometry of the cube
  xw <- cube_width
  yw <- cube_width
  
  # lower left corner of cube and height differences
  x1 <- cube_vec[1]
  y1 <- cube_vec[2]
  z0 <- cube_vec[3]
  z1 <- cube_vec[4]
  
  # cube face color
  curr_color <- column_colors[(z1* num_colors )+1]
  
  right_side <- matrix(c(x1,x1,x1,x1,z0,z0,z1,z1,y1,y1+yw,y1+yw,y1), 4,3)
  front_side <- matrix(c(x1,x1+xw,x1+xw,x1,z0,z0,z1,z1,y1,y1,y1,y1), 4,3)
  
  # transformation matrices
  y_tr  <- matrix(c(0,0,0,0,0,0,0,0,yw,yw,yw,yw), 4,3)
  x_tr  <- matrix(c(xw,xw,xw,xw,0,0,0,0,0,0,0,0), 4,3)
  
  # transformation of two cube plains (front side, rigth side) in both directions
  left_side <- right_side + x_tr
  back_side <- front_side + y_tr 
  
  rgl.quads(rbind(right_side,left_side,front_side,back_side), col=curr_color)
}


#' barplot3d
#'
#' Plotting 3D Bars
#' @param heigths_arr
#' @keywords plate readers
#' @export 
#' @examples
#'  barplot3d()
#' 
#' @note todo: testing scale; average growth curve plot; 96 well overview plots
#' 

barplot3d <- function(heights_arr, barcode = "0000", filename = "_3Dbarplot",
                      column_colors = 'default', bg_color='white',
                      color_types =FALSE, num_colors=20, 
                      theta = -60, phi=15, scale=1.0, width=700, height=900, transp = 1.0,
                      col_lab=NULL, row_lab=NULL, z_lab=NULL,
                      bar_width=0.5, bar_distance=0.8,
                      output_format='screen')
{
  # **** RGL settings
  rgl.open()
  save <- par3d(skipRedraw=TRUE)
  on.exit(par3d(save))
  
  # Choosing a background
  #rgl.bg(col="#cccccc") lightgrey
  #rgl.bg(color="gray")
  rgl.bg(color=bg_color)
  #rgl.light()
  rgl.pop("lights") 
  light3d(specular="black")
  
  #title3d('','',xlab='xlab',ylab='Abs/AU',zlab='ylab')
  title3d('','',ylab='Abs/AU')
  
  # alpha is transparency
  
  # **** scaling hights array
  heights_arr <- heights_arr * scale
  
  # **** selecting color scheme 
  # factor to spread colors over the whole range and +1 to prevent indexing by 0
  num_col <- ( max(heights_arr, na.rm=TRUE) * num_colors ) + 1 
  
  switch(column_colors,
         default={column_colors <-colorRampPalette(c("blue","green","yellow","red"))(num_col)},
         green={column_colors <-colorRampPalette(c("yellow","green","darkgreen"))(num_col)},
         red={column_colors <-colorRampPalette(c("yellow","red","darkred"))(num_col)},
         blue={column_colors <-colorRampPalette(c("lightblue","blue","darkblue"))(num_col)},
         heat={column_colors <- rev(heat.colors(num_col))}
  )
    
  nrows = as.integer(dim(heights_arr)[1])
  ncols = as.integer(dim(heights_arr)[2])
  nheights = as.integer(dim(heights_arr)[3])
    
  cat("n cols :", ncols, "- rows: ", nrows, '\n' )
  
  # spawning a 3D matrix for corner coordinates of the cuboids (12x8x2+n*z)
  ncubes = nrows * ncols
    
  x_distance <- bar_width + bar_distance
  y_distance <- bar_width + bar_distance
  
  rowm <- matrix(seq((nrows-1)*x_distance,0, -x_distance),nrows,ncols)
  colm <- matrix(seq(0,(ncols-1)*y_distance, y_distance), byrow=TRUE,nrows,ncols)
  
  cube_basism <- c(rowm,colm)
  cube_arr <- array(c(cube_basism, heights_arr), dim=c(nrows,ncols,2+nheights))

  # helper function for preparation of the cuboid colums
  axis <- TRUE  
  plotCuboidColumn <-function(cube_vec, cube_width, column_colors, num_colors=20)
  {  
    # cube geometry
    xw <- cube_width
    yw <- cube_width
    
    # lower left corner and height differences
    x1 <- cube_vec[1]
    y1 <- cube_vec[2]
    z0 <- cube_vec[3] # cuboid bottom height
    z1 <- cube_vec[length(cube_vec)] # cuboid lid hight
    
    # melting the coordinates to one matrix containing all cube coordinates
    num_heights <- length(cube_vec) - 1 
    h_combined <- sapply((3:num_heights), function(x) c(cube_vec[1],cube_vec[2],cube_vec[x], cube_vec[x+1]) )
    
    # plotting stack of cubes
    invisible(apply(h_combined, 2, cubeFactory, cube_width, column_colors ))
    
    # plotting bottom and lid
    bottom <- matrix(c(x1,x1+xw,x1+xw,x1,0,0,0,0,y1,y1,y1+yw,y1+yw), 4,3)
    z_tr  <- matrix(c(0,0,0,0,z1,z1,z1,z1,0,0,0,0), 4,3)
    
    curr_color <- column_colors[(z1*num_colors)+1]
    
    rgl.quads(bottom, col=curr_color)
    # and now the lid
    rgl.quads(bottom+z_tr, col=curr_color)
    #plot only axis for first plot
    if (axis == TRUE) {axis <<- FALSE }
  } 
  
  # plotting the cubes
  apply(cube_arr, c(1,2), plotCuboidColumn, bar_width, column_colors )
  
  # adding the axes and grid
  #axes3d(c('x','y','z'), expand=1.00)
  axes3d(c('y'), expand=1.00) 
  grid3d(side=c('x','z'))
  
  # well coordinates 
  row.names <- LETTERS[1:8]
  col.names <- as.character(1:12)
  
  text3d(x=rowm[,1]+0.2, y=-0.2, z=-0.5, texts=row.names ,col="black", cex=1.1)
  text3d(x=-0.6, y=-0.2, z=colm[1,], texts=col.names ,col="black", cex=1.1)
  
  ##par3d(userMatrix=um, FOV=19.28572,  c(0,0,1200,800)) # projection !
  par3d( FOV=19.28572)
  view3d(theta = -115, phi=25)
  
  switch(output_format,
         screen={},
         webGL={ out_filename_3D <- paste(barcode, filename, ".html", sep="" )
                 writeWebGL( dir="webGL", filename=file.path("webGL", out_filename_3D),  
                       template = system.file(file.path("WebGL", "template.html"), package = "rgl"), 
                       width=width, height=hight) 
               },
         png={ out_filename_3D <- paste(barcode, filename, ".png", sep="" )
              rgl.snapshot(out_filename_3D) },
         svg={ out_filename_3D <- paste(barcode, filename, ".svg", sep="" )
               rgl.postscript( filename=out_filename_3D, fmt="svg", drawText=TRUE ) },
         { cat(output_format, "- unknown output format specified - (supported formats: 'screen', 'webGL', 'png', 'svg') ") }
  )

  if(output_format %in% c('webGL', 'svg') ) rgl.close()
  return(TRUE)
}

#' platePlot3d
#'
#' @title Plotting 3D bars of Measurements in Microtiter Format
#' @description
#'    Wrapper function for 3D bar plotting 
#' @param heigths_arr
#' @keywords plate readers
#' @export 
#' @examples
#'  platePlot3d()
#' 
#' @note todo: 
#' 

platePlot3d <- function(heights_df, barcode = "0000", wavelength=0, use_slope=FALSE, filename = "_3Dbarplot",
                      column_colors = 'default', bg_color='white',
                      color_types =FALSE, num_colors=20, 
                      theta = -60, phi=15, scale=1.0, width=700, height=900, transp = 1.0,
                      col_lab=NULL, row_lab=NULL, z_lab=NULL,
                      bar_width=0.5, bar_distance=0.8,
                      output_format='screen')
{
  
  if(wavelength == 0) print("Warning: No wavelength specified !")
  
  # converting data frame to array for fast plotting
  heights_arr <- readerDF2Array(heights_df, wavelength=wavelength, use_slope=use_slope)
  
  barplot3d(heights_arr, barcode=barcode, filename=filename,
            column_colors=column_colors, bg_color=bg_color,
            color_types=color_types, num_colors=num_colors, 
            theta=theta, phi=phi, scale=scale, width=width, height=height, transp=transp,
            col_lab=col_lab, row_lab=row_lab, z_lab=z_lab,
            bar_width=bar_width, bar_distance=bar_distance,
            output_format=output_format)
  return(TRUE)
}
