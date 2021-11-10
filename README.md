# CellWalker
Morphological analysis tool for segmented 3D microscopy images of biological cells

### Installation

This program does not require specific installation procedure. The script is tested on Python 3.7 on Ubuntu 18.04.




The required packages can be found in the requirements.txt file.


# Under progress-
**User guide

Clone the github repository to your local system

Create python environment. This step is tested using Anaconda Python distribution (link). But it should be possible to use other python distributions as well.

Activate the newly created environment
```
conda activate cellwalker
```

Browse to the 'src' folder of the cloned repository and run the python script as follows<br>
python cellwalker.py

<p style="font-style: italics;" align="center">
<img height=300 src="cellwalker_blank.png" alt="CellWalker window" /><br>
CellWalker window
</p>


Loading segmented images (or segmentation masks)
Click on the 'Load segmentation' button.
A dialog box will open and allow selection of a folder.
Browse to the folder that contains the segmentation stored as images in PNG format.
At the moment, CellWalker can only read PNG image sequences. If you have a tiff image stack then you can use a software like ImageJ to generate an image sequence.
Also please note that the current version of CellWalker is designed to work with 8-bit grayscale segmentation images. If 24-bit RGB images are provided, then only the first channel will be used to detect segment labels.


Once inside the folder containing the images, click 'Ok'. A dialog box will popup asking if you want to continue loading the images. If you are certain that this is the folder you want to choose, click 'Ok'. Otherwise click 'Cancel'. Note that large image sequences can take considerably long time to load into CellWalker.

The images will now be loaded and the CellWalker will display the sequence of images in the segmentation frame. The colors assigned to the segments will be arbitrary. The segments identified by the CellWalker will be listed in the panel on the right side of the segmentation frame. The labels for the segments are derived from the actual pixel values. For example, a segment named 'Segment 121' is the segment with pixel values 121 in the original image.
The displayed colors of a segment can be changed by clicking on the colored button against the name of the segment.

Scrolling throught the image sequence is facilitated by the slider at the bottom of the segmentation frame. Scrolling is also possible using keyboard left and right arrows after clicking once on any segmentation image.


Using 'Merge List' and saving segments as 3D objects-

Skeletonization-
Using translation coordinates
Using erosion
Kimimaro parameters
Opening skeletons from SWC files
Viewing skeletons- downsampling, coloring by node radius / component, zoom, pan
Analysis of skeletons-
   Selecting nodes on skeleton
   Length measurement between two nodes
   Cross-sectioning of original images using skeleton- Using EM data and masks
   Curvature analysis
Saving skeletons as SWC and OBJ files
   Setting radius for edges and nodes
   


Find protrusions
   Deciding erosion and dilation iterations
   Output obj files - soma, protrusions

Segment propertise: Morphometric analysis of segments

Calculate planes separating selected objects




