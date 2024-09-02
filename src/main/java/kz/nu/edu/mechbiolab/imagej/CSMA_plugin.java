/*
 * To the extent possible under law, the ImageJ developers have waived
 * all copyright and related or neighboring rights to this tutorial code.
 *
 * See the CC0 1.0 Universal license for details:
 *     http://creativecommons.org/publicdomain/zero/1.0/
 */

package kz.nu.edu.mechbiolab.imagej;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Comparator;

import ij.ImagePlus;
import ij.ImageStack;
import ij.io.Opener;
import ij.plugin.PlugIn;

/**
 * @author Amina Sagymbayeva
 */

public class CSMA_plugin implements PlugIn{
	
    public void run(String arg) {
    	try {
    		PathWriter imgpaths = new PathWriter();
    		String outputDirectory = imgpaths.get();
	    	PythonLauncherWin launcherWin = new PythonLauncherWin();
	    	int launchExitCode = launcherWin.condaExecutePython();
	    	if (launchExitCode == 0 && outputDirectory != null) {
	            File parentDir = new File(outputDirectory);
	            File[] subDirectories = parentDir.listFiles(File::isDirectory);
	            File latestSubfolder = null;
	            long latestModifiedTime = Long.MIN_VALUE;
	            for (File subFolder : subDirectories) {
	                long lastModified = subFolder.lastModified();
	                if (lastModified > latestModifiedTime) {
	                    latestModifiedTime = lastModified;
	                    latestSubfolder = subFolder;
	                }   	                
	            }
	            	File[] pngFiles = latestSubfolder.listFiles((dir, name) -> name.toLowerCase().endsWith(".png"));
	            	Arrays.sort(pngFiles, Comparator.comparingLong(File::lastModified));
	                // Create an ImageStack to hold the images.
	                ImageStack stack = new ImageStack();
	                // Use ImageJ's Opener to open each image in the sequence.
	                Opener opener = new Opener();
	                for (File pngFile : pngFiles) {
	                    ImagePlus image = opener.openImage(pngFile.getPath());
	                    if (image != null) {
	                        // Add image to the stack
	                        stack.addSlice(pngFile.getName(), image.getProcessor());
	                    }
//	                    } else {
//	                        // Print an error message if any image couldn't be opened
//	                        IJ.log("Failed to open image: " + pngFile.getPath());
//	                    }
	                }
	                // Create an ImagePlus object using the stack
	                ImagePlus imageSequence = new ImagePlus("Image Sequence", stack);
	                // Display the image sequence stack
	                imageSequence.show();
//	            } else {
//	                // Print an error message if no subfolders were found
//	                IJ.log("No subfolders found in directory: " + outputDirectory);
//	            }
	    	}
		} catch (IOException|NullPointerException | InterruptedException e) {
			e.printStackTrace();
		} 
    }
}