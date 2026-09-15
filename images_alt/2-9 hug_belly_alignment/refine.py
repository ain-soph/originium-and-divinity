from PIL import Image
import numpy as np
from scipy.ndimage import binary_erosion,binary_dilation, gaussian_filter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_flow,breadth_first_order
from pathlib import Path
p=Path('/Users/local0state/docker/docs/源石与神灵');o=p/'images_alt/hug_belly_alignment'
a=np.array(Image.open(p/'第二卷 十字军之神/2-9 hug.png')).astype(float);b=np.array(Image.open(o/'aligned.png')).astype(float)
m=np.load(o/'trial.mask.npy'); box=(slice(825,1145),slice(390,1040));s=m[box];h,w=s.shape;n=h*w
inner=binary_erosion(s,iterations=20,border_value=1); outer=binary_dilation(s,iterations=20)
d=np.sqrt(np.mean((a[box]-b[box])**2,axis=2));d=gaussian_filter(d,.6)
# Find a low-discontinuity boundary only within a band around the visually drawn region.
ix=np.arange(n).reshape(h,w);rows=[];cols=[];vals=[]
for aa,bb in [(ix[:,:-1],ix[:,1:]),(ix[:-1],ix[1:])]:
 cost=(1+((d.ravel()[aa]+d.ravel()[bb])/2)**2).astype(np.int64)
 for r,c in [(aa,bb),(bb,aa)]:rows.append(r.ravel());cols.append(c.ravel());vals.append(cost.ravel())
for target,ids in [(n,np.flatnonzero(inner)),(n+1,np.flatnonzero(~outer))]:
 rows.append(np.full(ids.size,target));cols.append(ids);vals.append(np.full(ids.size,100000000,dtype=np.int64))
 rows.append(ids);cols.append(np.full(ids.size,target));vals.append(np.full(ids.size,100000000,dtype=np.int64))
g=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(n+2,n+2)).tocsr()
f=maximum_flow(g,n,n+1);res=g-f.flow;res.data=(res.data>0).astype('int8');res.eliminate_zeros();reachable=breadth_first_order(res,n,directed=True,return_predecessors=False)
t=np.zeros(n+2,bool);t[reachable]=1;final=np.zeros_like(m);final[box]=t[:n].reshape(h,w);np.save(o/'refined.npy',final)
