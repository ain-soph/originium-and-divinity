from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.optimize import least_squares
from pathlib import Path
p=Path('/Users/local0state/docker/docs/源石与神灵')
out=p/'images_alt/hug_belly_alignment'
a=np.array(Image.open(p/'第二卷 十字军之神/2-9 hug.png').convert('RGB'))
b=np.array(Image.open(p/'images_alt/2-9 hug (small belly).png').convert('RGB'))
ag=gaussian_filter(a.mean(2),1.5); bg=gaussian_filter(b.mean(2),1.5)
y,x=np.mgrid[630:1080:4,500:1000:4]
m=((y<850)| (x<570)|(x>930))
x=x[m];y=y[m]; ref=ag[y,x]
def coords(v,x,y):
 u=x-750;w=y-850
 return v[0]*u+v[1]*w+750+v[4],v[2]*u+v[3]*w+850+v[5]
def residual(v):
 xx,yy=coords(v,x,y)
 return map_coordinates(bg,[yy,xx],order=1)-ref
fit=least_squares(residual,[.982,0,0,.982,-13,-15],bounds=([.9,-.08,-.08,.9,-60,-70],[1.08,.08,.08,1.08,60,60]),loss='soft_l1',f_scale=10,max_nfev=130)
print(fit.x, np.mean(abs(residual(fit.x))))
yy,xx=np.mgrid[:a.shape[0],:a.shape[1]]; bx,by=coords(fit.x,xx,yy)
aligned=np.stack([map_coordinates(b[:,:,c].astype(float),[by,bx],order=3,mode='nearest') for c in range(3)],2).clip(0,255).round().astype('uint8')
Image.fromarray(aligned).save(out/'aligned.png')
np.save(out/'inverse_affine.npy',fit.x)
# inspection of original and aligned at equal coordinates
box=(480,770,1010,1120)
crops=[Image.fromarray(v).crop(box) for v in [a,aligned]]
panel=Image.new('RGB',(1060,350));panel.paste(crops[0],(0,0));panel.paste(crops[1],(530,0));panel.save(out/'comparison.png')
