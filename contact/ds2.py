import struct

def read_tst_file(filename):
    "Reads a .tst file from a bruker UMT machine"
    data=dict()
    with open(filename, 'rb') as file:
        metadata=dict()
        while True:
            number, name, value = split_line(file)
            if name is None:
                break
            metadata[name]=value
                
            if name=='channelsarray':
                channels=[]
                for i in range(value):
                    channels.append(read_channel(file))
                metadata['channels']=channels #no other names can have # in
        # meta data for the whole file has been read
        data['metadata']=metadata
        # next the data for each run is read
        n_runs=metadata['runs']
        run_data=[]
        for run in range(n_runs):
            run_data.append(read_run(file, metadata))
        data['run_data']=run_data
    return data


def read_run(file, file_metadata):
    """
    Reads a 'run' of a script
    """
    # first read the run meta data
    run_data=dict()
    number, name, value = split_line(file)
    metadata=dict()
    if name!='run':
        raise ValueError("This is not a run")
    metadata[name]=value
    file.readline()# one empty line before run starts
    while True:
        number, name, value = split_line(file)
        if name is None:
            break
        metadata[name]=value
    #all the metadata for the run has been read in 
    run_data['metadata']=metadata
    
    #then read each step
    n_steps=file_metadata['steps']
    
    steps=[]
    for i in range(n_steps):
        steps.append(read_step(file,file_metadata,metadata))
    run_data['steps']=steps
    return run_data
    
def read_step(file, file_metadata, run_metadata):
    """ reads a step of the test"""
    number, name, value = split_line(file)
    metadata=dict()
    if name is None: #for steps other than the first there is 2 lines of stars
        number, name, value = split_line(file)
    if name != 'test':
        raise ValueError("This is not a run")
    metadata[name]=value
    while True:
        number, name, value = split_line(file)
        if name is None:
            break
        metadata[name]=value
    
    while True:
        number, name, value = split_line(file)
        if name is None:
            break
        metadata[name]=value
    
    if metadata['isdata']:
        step_data=read_data(file, file_metadata, run_metadata, metadata)
    else:
        step_data=None
    return {'metadata':metadata, 'data':step_data}

def read_data(file, file_metadata, run_metadata, step_metadata):
    """ reads the data from the file """
    channels=file_metadata['channels']
    samples=step_metadata['samples']
    chan_lens=[c['lengthinbytes'] for c in channels]
    chan_names=[c['name'] for c in channels]
    data={cn:[] for cn in chan_names}
    for sample in range(int(samples)):
        for name, chan_len in zip(chan_names, chan_lens):
            data[name].append(struct.unpack('d',file.read(chan_len))[0])
        file.read(1)
    return data
    

def read_channel(file):
    channel_data=dict()
    name=''
    while name!='type':
        number, name, value = split_line(file)
        channel_data[name]=value
    return channel_data
        
def split_line(file):
    line_str = file.readline().decode()
    number,*rest=line_str.split('#')[1:]
    rest=''.join(rest)
    number=number.strip(' ')
    name,value=rest.split('$')[0:2]
    name=name.strip(' ')
    
    if name.strip('*')=='':
        name=None
    else:
        name=name.lower()
    if value=='':
        value=None
    elif number in ['28', '31']:
        value=int(value)
    elif number in ['33','37','38']:
        value=float(value)
    number=int(number)
    
    return number, name, value

if __name__=='__main__':
    filename=r"I:\UMT\Mike\17May2019\testdata-1.tst"
    data=read_tst_file(filename)
    