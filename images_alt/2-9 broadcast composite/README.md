# Broadcast 局部合成

result.final.png 为成品，1448 × 1086。原图为底，只选入新翅膀以及清除旧翅膀所需的白底。原始输入不覆盖。

原图 1448 × 1086，修复图 1447 × 1087。先仅将修复图用 Lanczos 对齐到原图尺寸；再清理翼根下方新图变直的腰背与旧羽毛重叠的小区域，用修复图同一高度、向右 80 像素处的气泡白底复制填入。具体选区见 preparation.json。这一步生成 prepared-repair.png，因此成品不是两张未处理输入的直接二选一。

随后按 regions.json 手工多边形，用 composite-local-image-repairs/scripts/composite.py 做严格布尔合成；不羽化、不整体调色或锐化。选区外逐像素等于原图，选区内逐像素等于 prepared-repair.png；详见 verification.json。全图和放大翼根已目视检查。

result.mask.npy 是二维 bool 遮罩；result.mask.png 是索引值 0/1 的预览遮罩；result.overlay.png 青色表示选区；comparison.png 从左到右为原图、修翅膀图、合成图。
