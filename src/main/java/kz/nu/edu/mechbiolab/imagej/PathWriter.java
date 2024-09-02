package kz.nu.edu.mechbiolab.imagej;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

import ij.ImagePlus;
import ij.ImageStack;
import ij.WindowManager;
import ij.gui.GenericDialog;

public class PathWriter {
	public String get() throws IOException {
		String directoryPath = null;
        File tempFile = null;
		try {		
			
			int[] windowList = WindowManager.getIDList();
		    if (windowList == null || windowList.length == 0) {
		        throw new NullPointerException("NoImagesOpen");
		    }
            tempFile = File.createTempFile("canny_temp_imglist", ".txt");
            String filePath = tempFile.getAbsolutePath(); 
            PrintWriter writer = new PrintWriter(new FileWriter(filePath));
	        for (int folderID : windowList) {
	            ImagePlus folder = WindowManager.getImage(folderID);
	            directoryPath = folder.getOriginalFileInfo().directory;
	            String folderPath = folder.getOriginalFileInfo().directory + folder.getOriginalFileInfo().fileName;
	            ImageStack stack = folder.getStack();
	            int numFrames = stack.getSize();
	            for (int i = 1; i <= numFrames; i++) {
	                String slicePath = stack.getSliceLabel(i);
	                writer.println(folderPath+slicePath);
		        }
		    }
	        writer.close();
	    } catch (NullPointerException|IOException e) {
			if (e.getMessage()=="NoImagesOpen") {
				GenericDialog gd = new GenericDialog("Error Message");
				gd.setInsets(5,15,0);
				gd.addMessage("Please load the image stack first.");
				gd.setInsets(5, 10, 0);
				gd.showDialog();
			}
	    } finally {
			tempFile.deleteOnExit();
	    }
		return directoryPath;
	}
}
