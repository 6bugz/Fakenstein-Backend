# Fakenstein-Backend

To set up the backend:

- Import packages listed in requirements.txt to a virtual environment:
  With virtualenv:
  - pip install virtualenv
  - virtualenv <env_name> 
  - source <env_name>/bin/activate
  - pip install -r requirements.txt

  With conda:
  - conda create --name <env_name> python = < version >
  - pip install requirements.txt

- It is advised to use a virtual environment with a Python version of 3.7 or
higher to not face error in the installation of the requirements.
  
- Conda can be used to prevent any package version/python version conflicts
in the virtual environment.
  
- Depending on the compilers you have, you may or may not face a problem
with compiling certain Python libraries that were originally developed in C/C++. Please refer to the official websites and documentations of those packages and follow the setup instructions for your respective environment if you run into any problems.
  
- Activate the virtual environment
   With virtualenv:
      source <env_name>/bin/activate
  With conda:
      conda activate <env_name>
  
-  Run the Flask application (app.py) with the following command:
  flask run –host=0.0.0.0

