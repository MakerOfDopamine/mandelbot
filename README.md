# mandelbot
 A bot that finds interesting Mandelbrot areas!

# Currently Available
I currently have a basic renderer doing the basic iteration of z <- z^2 + c on each pixel before drawing them to the screen. 
I thought that I should probably write this throughout the devlogs so it doesn't get flagged for AI gen again. From the last modification I have restricted the coloring from generating a hue above 0.9 so that the edge colors stay at violet and don't loop back to red.

# Using the tool
- Click and drag on the screen to draw a bounding box to zoom in. (This is clipped to aspect ratio)
- Press ESC to cancel a drawn box.
- Press -/= to decrease/increase iterations by 0.8x/1.2x.
- Press ALT+above to decrease/increase iterations by 0.5x/2x.