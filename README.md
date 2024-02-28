# worth
Wyoming Outdoor Recreation, Tourism and Hospitality (Initiative) - SoC code repository

### Setup Python

1. Download and setup a conda environment using [miniforge](https://github.com/conda-forge/miniforge#miniforge3). Then, activate your conda environment at the command line terminal with:

```
conda activate
```

2. Using git to clone this github repository:

```
git clone git@github.com:WyoSoC/worth.git
```

For those unfamiliar with CLI, use a git GUI such as GitHub Desktop or the git interface in VS Code to clone the repo to your desired location.

Throughout the development, remember to run `git pull` frequently to keep your local repo in sync.

3. Navigate to the 'worth' directory (`cd` in or open the directory in your IDE of choice) and issue the following command to create a new virtual environment called "worth". This will pull all necessary libraries and dependencies together. We recommend [VS Code](https://code.visualstudio.com/download) as a good modern IDE.

```
conda env create -f environment.yml
```

```
conda activate worth
```

### Streamlit Web-App

Command to activate a local server using Streamlit:

```
streamlit run my_app.py
```

### Using GitHub and SSH

You may need to [set up SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent?platform=windows) in order to connect securely to GitHub.

GitHub has a file size limit of 100MB. If we accidentally try to push a file too large, it will fail. The following command will back off 1 commit so that we can fix the file size and try the commit again.

```
git reset --soft HEAD~1
```
