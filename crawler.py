import json
import numpy as np
import urllib.request
import os
import yaml


def has_allviews(ant_images):
    for imkey in ant_images.keys():
        im = ant_images[imkey]
        if 'h' in im['shot_types'] and 'p' in im['shot_types'] and 'h' in im['shot_types']:
            return True
    
    return False
    
def has_someview(ant_images):
    for imkey in ant_images.keys():
        im = ant_images[imkey]
        if 'h' in im['shot_types'] or 'p' in im['shot_types'] or 'h' in im['shot_types']:
            return True
    
    return False

def load_specimens(genus):
    batch = 1000
    target_url = 'http://www.antweb.org/api/v2/?genus='+genus+'&limit=10'
    with urllib.request.urlopen(target_url) as url:
        json1_str = url.read()
        count = json.loads(json1_str)['count']
    
    print(genus+'has '+str(count)+' specimens')
        
    genusspec = []
    for mult_offset in range(count//batch+1*(count%batch>0)):
        target_url = 'http://www.antweb.org/api/v2/?genus='+genus+'&limit='+str(batch)+'&offset='+str(mult_offset*batch)
        with urllib.request.urlopen(target_url) as url:
            json1_str = url.read()
            genusspec += json.loads(json1_str)['specimens']
    return genusspec

def build_genusdb(genuses, min_spec=3):
    genusdb = {}
    for genus in genuses:
        print('dowloading '+genus+' information...')
        genusspec = load_specimens(genus)
        if "empty_set" in genusspec:
            continue
        n = 0
        specimes = []
        specimes_comp = []

        for ant in genusspec:
            try:
                if has_allviews(ant['images']):
                    n+=1
                    specimes+=[ant['catalogNumber']]
                elif has_someview(ant['images']):
                    n+=1
                    specimes_comp+=[ant['catalogNumber']]
            except:
                pass
            
        print(genus+'has '+str(n)+'specimens with images')
           
        if n>=min_spec:
            print('Genus included because it has at least '+str(min_spec)+' specimens with images.')
            genusdb[genus]={'specimes':specimes, 'specimes_comp':specimes_comp}
    return genusdb
            
def load_allgenus():
    with open('antweb_genus.txt','r') as f:
        genuses_raw = [line.strip() for line in f.readlines()]
        
    return genuses_raw

def download_ants(genuses_list, path='antweb/'):        
    try:
        with open('genusdb.yaml','r') as filee:
            genusdb = yaml.load(filee)
    except:
        genusdb = build_genusdb(genuses_list)
        with open('genusdb.yaml','w') as filee:
            filee.write(yaml.dump(genusdb, default_flow_style=False))
    
    imgdb_genus = {}
    imgdb_specie = {}
    for gen in list(genusdb.keys()):
        print('Downloading', gen)
        imgdb_genus[gen] = {}
        
        genusspec = load_specimens(gen)
            
        for antspec in genusspec:
            if not antspec['catalogNumber'] in genusdb[gen]['specimes'] + genusdb[gen]['specimes_comp']:
                continue
            currentold = antspec['catalogNumber']
            current = antspec['catalogNumber']
        
            if ' ' in current:
                a,b,c = str(current).split(' ')
                current = str(a)+'('+b+')'+c        
            
            
            images = antspec['images']
            specie = antspec['scientific_name'].replace(' ', '_')
            idd = current
                    
            if not os.access(path,os.F_OK):
                os.mkdir(path)
                
            imgdb_genus[gen][current] = []            
            if not specie in imgdb_specie:
                imgdb_specie[specie] = {}
            imgdb_specie[specie][current] = []
            
            
            for imkey in sorted(images.keys()):
                for shott in images[imkey]['shot_types'].keys():
                    if shott in ['p','h','d']:
                        for im in images[imkey]['shot_types'][shott]['img']:
                            im = im.replace(currentold, current)
                            if 'high' in im:
                                imgn = im.split('/')[-1]
                                imgdb_genus[gen][current]+=[imgn]
                                imgdb_specie[specie][current]+=[imgn]
                                if not os.access(path+gen,os.F_OK):
                                    os.mkdir(path+antspec['genus'])
                                if not os.access(path+gen+'/'+idd,os.F_OK):
                                    os.mkdir(path+antspec['genus']+'/'+idd)
                                if not os.access(path+antspec['genus']+'/'+idd+'/'+imgn,os.F_OK):
                                    print(gen, im)
                                    urllib.request.urlretrieve(im,path+antspec['genus']+'/'+idd+'/'+imgn)
                                    
    with open('imgdb_genus.yaml','w') as filee:
        filee.write(yaml.dump(imgdb_genus, default_flow_style=False))
        
    with open('imgdb_specie.yaml','w') as filee:
        filee.write(yaml.dump(imgdb_specie, default_flow_style=False))
        
def download_allants():
    genuses_list = load_allgenus()
    download_ants(genuses_list)

def exactly_3views(antlist):
    if len(antlist)!=3:
        return False
    else:
        someh = False
        somep = False
        somed = False
        for img in antlist:
            
            if '_h_' in img:
                someh = True
            if '_p_' in img:
                somep = True
            if '_d_' in img:
                somed = True
            
        if someh and somep and somed:
            return True
        else:
            return False

def genusmap(genuss,genus):
    return str(genuss.index(genus))


def dataset_split_tvt(path, specmin, testr = 0.1, valr = 0.2):
    with open('imgdb_genus.yaml','r') as filee:
        imgdb_genus = yaml.load(filee)
    
    train = []
    trainh = []
    traind = []
    trainp = []
    
    val = []
    valh = []
    vald = []
    valp = []
    
    test = []
    testh = []
    testd = []
    testp = []
    
    abnorm = []
    abnormh = []
    abnormd = []
    abnormp = []
    
    genuss = []
    genuss_out = []
    
    for genus in imgdb_genus.keys():
        n = len(imgdb_genus[genus])
        if n>=specmin:
            genuss.append(genus)
            
            testn = int(n*testr)
            valn = int(n*valr)
            complete = []
            ncomp = []
            for key_spec in imgdb_genus[genus].keys():
                specim = imgdb_genus[genus][key_spec]
                if exactly_3views(specim):
                    complete+=[key_spec]
                else:
                    ncomp+=[key_spec]
                    
        
            tvt_complete = list(np.random.permutation(complete))
            
            testspec = tvt_complete[:int(testn)]
            tv_complete = tvt_complete[int(testn):]
            
            valspec = tv_complete[:valn]
            t_complete = tv_complete[valn:]
            
            trainspec = ncomp+t_complete
            
            for key_spec in testspec:
                for img in imgdb_genus[genus][key_spec]:
                    test+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    
                    if '_h_' in img:
                        testh+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    if '_p_' in img:
                        testp+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    if '_d_' in img:
                        testd+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    
            for key_spec in valspec:
                for img in imgdb_genus[genus][key_spec]:
                    val+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
    
                    if '_h_' in img:
                        valh+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    if '_p_' in img:
                        valp+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    if '_d_' in img:
                        vald+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    
            for key_spec in trainspec:
                for img in imgdb_genus[genus][key_spec]:
                    train+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    
                    if '_h_' in img:
                        trainh+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    if '_p_' in img:
                        trainp+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
                    if '_d_' in img:
                        traind+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss, genus)]]
        else:
            genuss_out.append(genus)
            for key_spec in imgdb_genus[genus].keys():
                specim = imgdb_genus[genus][key_spec]
                abnormspec = []
                if exactly_3views(specim):
                    abnormspec+=[key_spec]
            
            for key_spec in abnormspec:
                for img in imgdb_genus[genus][key_spec]:
                    abnorm+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss_out, genus)]]
                    
                    if '_h_' in img:
                        abnormh+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss_out, genus)]]
                    if '_p_' in img:
                        abnormp+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss_out, genus)]]
                    if '_d_' in img:
                        abnormd+=[[genus+'/'+key_spec+'/'+img,genusmap(genuss_out, genus)]]
    
    with open(path+'synset_words.txt', 'w') as f:
        for row in genuss:
            f.write(row+'\n')
            
    with open(path+'synsets.txt', 'w') as f:
        for row in genuss:
            f.write(row+'\n')
    
    with open(path+'dataset_train.txt', 'w') as f:
        for row in train:
            f.write(" ".join(row)+'\n')

    with open(path+'dataset_trainh.txt', 'w') as f:
        for row in trainh:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_traind.txt', 'w') as f:
        for row in traind:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_trainp.txt', 'w') as f:
        for row in trainp:
            f.write(" ".join(row)+'\n')
    
    
    with open(path+'dataset_val.txt', 'w') as f:
        for row in val:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_valh.txt', 'w') as f:
        for row in valh:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_vald.txt', 'w') as f:
        for row in vald:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_valp.txt', 'w') as f:
        for row in valp:
            f.write(" ".join(row)+'\n')
            
            
    with open(path+'dataset_test.txt', 'w') as f:
        for row in test:
            f.write(" ".join(row)+'\n')

    with open(path+'dataset_testh.txt', 'w') as f:
        for row in testh:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_testd.txt', 'w') as f:
        for row in testd:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_testp.txt', 'w') as f:
        for row in testp:
            f.write(" ".join(row)+'\n')
            
            
            
    with open(path+'dataset_abnorm.txt', 'w') as f:
        for row in abnorm:
            f.write(" ".join(row)+'\n')

    with open(path+'dataset_abnormh.txt', 'w') as f:
        for row in abnormh:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_abnormd.txt', 'w') as f:
        for row in abnormd:
            f.write(" ".join(row)+'\n')
            
    with open(path+'dataset_abnormp.txt', 'w') as f:
        for row in abnormp:
            f.write(" ".join(row)+'\n')
            
if __name__ == '__main__':
    print('Wait ... building dataset, it might take a while.')
    genuses_list = load_allgenus()
    build_genusdb(genuses_list)
    print('Done.')
    
    print('Choose the option:')
    print('Warning: Dowloading images generates a yaml db of the imagens overwriting the last one.')
    print('(1) Download all Acanthognathus specimens and images to test (on antweb folder).')
    print('(2) Download all default genus, specimens and images (on antweb folder).')
    print('(3) Split dataset.')
    option = input('Insert option:')
    if option==1:
        download_ants(['Acanthognathus'])
    elif option==2:
        download_allants()
    elif option==3:
        dataset_split_tvt('newsplit/', 143, testr = 0.1, valr = 0.2)