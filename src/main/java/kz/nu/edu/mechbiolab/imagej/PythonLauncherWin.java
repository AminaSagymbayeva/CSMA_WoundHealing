package kz.nu.edu.mechbiolab.imagej;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import ij.gui.GenericDialog;

public class PythonLauncherWin {
	public File createTempFile(String resourceFile, String name, String fileFormat) throws InterruptedException, IOException, NullPointerException{
        File tempFile = null;
        InputStream input = getClass().getResourceAsStream(resourceFile);

        String tempFileName = "temp" + name + fileFormat;
        File tempDir = new File(System.getProperty("java.io.tmpdir"));
        tempFile = new File(tempDir, tempFileName);
        tempFile = File.createTempFile("temp" + name, fileFormat, tempDir);
        
        try (FileOutputStream out = new FileOutputStream(tempFile)) {
            int read;
            byte[] bytes = new byte[1024];
            while ((read = input.read(bytes)) != -1) {
                out.write(bytes, 0, read);
            }
            out.flush();
        } finally {
            input.close();
        }
        return tempFile;
    }
	
    private String findPython(String envName) throws InterruptedException, IOException {
        String path = null;
    	String[] condaFindCommand = new String[]{"cmd", "/c", "conda", "activate", envName, "&&", "where", "python"};
    	
//    	String[] condaInitCommand = new String[]{"conda", "init", "cmd"};    	
//    	ProcessBuilder initProcessBuilder = new ProcessBuilder(condaInitCommand);
//        Process initProcess = initProcessBuilder.start();
//        int initExitCode = initProcess.waitFor(); 
//        logger.info("conda init command exited with code: "+initExitCode);
//        if (!(initExitCode==2)) {
//        	throw new IOException("CondaNotRecognized");
//        	}
        
        ProcessBuilder findProcessBuilder = new ProcessBuilder(condaFindCommand);
        findProcessBuilder.redirectErrorStream(true);
        Process findProcess = findProcessBuilder.start(); 
        InputStream findInputStream = findProcess.getInputStream(); 
        BufferedReader findReader = new BufferedReader(new InputStreamReader(findInputStream));
        
        String line;
        while ((line = findReader.readLine()) != null) {
        	if (line.contains("EnvironmentNameNotFound")) {
            	findProcess.waitFor();
            	findInputStream.close();
        		findReader.close();
        		throw new IOException("Please install the environment first.");
        	} else if(line.contains(envName)) {
                path = line;
                break;
        	} else {
            	findProcess.waitFor();
            	findInputStream.close();
        		findReader.close();
        		throw new IOException("Please check Anaconda installation.");
        	}
        }
        
    	findProcess.waitFor();
    	findInputStream.close();
		findReader.close();
		return path;
    }
	    
	public int condaExecutePython() throws InterruptedException, IOException {
		File tempPythonFile = null;
		String envName = "ImageJCSMA";
		String pythonScript = "/image_processing.py" ;
		int exitCode = -1;
		
	    try {
	    	tempPythonFile = createTempFile(pythonScript, "pythonscript", ".py");
	    	
	        String tempPythonPath = tempPythonFile.getAbsolutePath();
	
	    	String pythonPath = findPython(envName);
		    String[] condaExecuteCommand = new String[]{"cmd", "/c", "conda", "activate", envName, "&&", pythonPath, tempPythonPath}; 			
            
		    ProcessBuilder processBuilder = new ProcessBuilder(condaExecuteCommand);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();
            InputStream inputStream = process.getInputStream();
            BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
            
            String line;
            while ((line = reader.readLine()) != null) {
            	if (line.contains("ModuleNotFoundError")) {
                    inputStream.close();
                    reader.close();
                    exitCode = process.waitFor();
                	throw new IOException("Error during the environment installation. Please reinstall the environment.");
            }
            }
            
            inputStream.close();
            reader.close();
            exitCode = process.waitFor();
           
            if (exitCode == 0) {
            } else {
            	throw new IOException();
            }
            tempPythonFile.delete();
            
	    } catch (IOException|InterruptedException|NullPointerException e) {
	    	raiseErrorWindow(e.getMessage()); 
	    	tempPythonFile.deleteOnExit();
	    } 
		return exitCode;
	}
  
    private static void raiseErrorWindow(String errorMessage) {
//      source: https://www.tabnine.com/code/java/classes/ij.gui.GenericDialog
		GenericDialog gd = new GenericDialog("Error Message");
		gd.setInsets(5,15,0);
		gd.addMessage(errorMessage);
		gd.setInsets(5, 10, 0);
		gd.showDialog();
		if (gd.wasCanceled()) {
			System.exit(0);
  	    }
	}
}
