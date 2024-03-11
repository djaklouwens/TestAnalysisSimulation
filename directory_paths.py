import os

# main project directory
project_dir = os.path.dirname(__file__)

# figures directory
plot_dir = project_dir + '/plots/'

# temp directory
temp_dir = project_dir + '/temp/'

# directory list
dir_lst = [plot_dir, temp_dir]

for idir in dir_lst:
    if not os.path.exists(idir):
        os.mkdir(idir)


illegal_char = r'[<>:"\\/|?¿*]'