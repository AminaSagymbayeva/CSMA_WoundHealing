# CSMA: an ImageJ Plugin for the Analysis of Wound Healing Assays

## Project Description
CSMA is an ImageJ plugin for the analysis of wound healing (scratch) assays. CSMA performs wound edge detection on a stack of consecutive images and calculates the area or the average width of the wound. It improves on the existing scratch assay analysis tools by accurately detecting migrating cells in the middle of the wound, providing a user-friendly interface, reducing image analysis time, and allowing the adjustment of multiple parameters to suit various imaging conditions. CSMA produces a .csv file with the wound area or width for every image, a graph of wound closure VS time, and images with detected wound area.


## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Fine-tuning](#fine-tuning)
- [Contributing](#contributing)
- [License](#license)


## Installation
1.	Install [ImageJ software](https://imagej.net/downloads).
2.	Install [Anaconda package](https://docs.anaconda.com/free/anaconda/install/index.html). **Please check ‘Add to system PATH’ option during installation.**
3.	Run the CSMAenv_installer to create a virtual environment with all the necessary libraries. Alternatively you can create the environment from .yml file provided in resources to this project. This prevents library version incompatibility and protects other projects should they have different library versions.
4.	From the target folder, download CSMA_WoundHealingTool-0.1.0.jar file.
5.	In the Plugins menu of ImageJ, select Install.
6.	Navigate to the folder with your jar file and select it. CSMA Wound Healing Tool should appear in the menu.


## Usage
1.	Prepare your dataset. **Ensure that the files are named in proper order (if your image is named ‘image2’, rename it to ‘image02’) and have the same format and dimensions.** Save all images to a single directory. Please try to select quality images as it will make the detection much easier.
2.	To open the image stack, select File>>Import>>Image Sequence and choose your dataset directory.
3.	When the image stack is loaded, select Canny Scratch Analysis from the Plugins menu.
4.	Adjust parameters accordingly. We recommend using the default parameter values on the first try. In case you want to improve the quality of wound detection, the instructions for fine-tuning the parameters might be a useful guide.
5.	Navigate to the directory with the original images; there you should find the processed images, a line graph, and a .csv file.


## Fine-tuning
1. ***Image contrast***: To change the contrast of the image, adjust the contrast limit and square grid size parameters. If you want to increase the contrast, try to increase both parameters (as a rule of thumb, step of 10 for coarse adjustment; step of 5 for precise adjustment). Tip: set higher contrast for wound boundary detection to detect as many cells at the edge as possible and lower contrast for cells detection to minimize the noise.
2. ***Dilation and erosion for edges***: To create continuous wound boundaries, the algorithm fuses the cells by increasing their radii, and then erodes them back. If the confluency of cells is low, try to increase the dilation rad parameter (values of less than 10 with a step of 0.5 is generally enough). It is a good practice to keep erosion rad slightly smaller to avoid overestimating the wound boundary.
3. ***Dilation and erosion for cells inside the wound***: The same erosion-dilation method is used to make continuous boundaries of cells inside the wound. However, dilation and erosion rad parameters values should be smaller. Choosing too large values will result in fused cell borders. Therefore, try to keep them as low as possible. Often values for erosion and dilation rad are the same. However, sometimes it is better to keep dilation rad slightly smaller (by 1 or 2) to remove noise inside the wound.  
If there are holes inside the detected cells try to increase the cell filling radius. 
4. ***Accounting for a slight field of view shift***: because the algorithm works by overlaying a mask from the previous image to the current image, slight shifts in the fields of view might result in the overestimation of one side of the wound boundary. To minimize the overestimation, try to increase the mask erosion rad and iterations values. Increasing the mask erosion parameter values often requires increasing the edge dilation rad simultaneously. Note that significant shifts in the field of view cannot be fixed in this way. 
5. ***Threshold***: to differentiate between true wound boundary and noise, we set a threshold value that represents the share of the top largest individual edges that will be detected as wound edges. The smaller this threshold, the less individual edges will be selected. 


## Contributing
All interested parties are welcome to contribute to this project. The code was developed in both Python 3 and Java programming languages. Python 3 is used for image processing and user interface (UI) development, whereas Java facilitates communication between ImageJ and Python. The algorithm was integrated as an ImageJ plugin to facilitate its spread among users accustomed to ImageJ.

### Detailed Breakdown

1. **How to Contribute**:
   - **Fork the Repository**: Click on the "Fork" button at the top right of the repository page to create your own copy of the repository. 
   - **Clone Your Fork**: lone your forked repository to your local machine. ```sh git clone https://github.com/your-username/your-repo-name.git
   - **Create a Branch**: `git checkout -b feature-name`.
   - **Make Your Changes**.
   - **Commit Your Changes**: 
git add .
git commit -m "Description of your changes"


   - **Push to Your Fork**: `git push origin feature-name`.
   - **Open a Pull Request**.

2. **Reporting Issues**:
If you encounter any issues or have questions, feel free to open an issue. We would appreciate if you provide as many details as possible to address the issue effectively.


## License
This project is licensed under the MIT License - see the [LICENSE](https://mit-license.org/) file for details.
