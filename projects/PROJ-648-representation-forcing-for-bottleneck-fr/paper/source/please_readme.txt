Version 0.9.4

1. arxiv使用latex编译不通过，转换成pdflatex编译
（.cls文件的\pdfoutput=1）
2. 添加了目录功能，paper.tex中的 \tableofcontents
不需要目录注释掉就可以
3. 优化Appendix字体大小




Version 0.9.3

1. 增加了双栏的option


如何快速替换？

1. 替换bytedance_seed.cls文件为最新。
2. 将paper.tex里面\documentclass修改一下

单栏: \documentclass[]{bytedance_seed}, 
%Please prioritize using single-column。

双栏: \documentclass[twocolumn]{bytedance_seed}




Version 0.9.2

1. \citet{}没法使用



如何快速替换？

1. 替换bytedance_seed.cls文件为最新。
2. 将paper.tex里面
%%%%%%%%%%%%%%%%%%%%%%
\bibliographystyle{plain}
\bibliography{main}
%%%%%%%%%%%%%%%%%%%%%%

换成
%%%%%%%%%%%%%%%%%%%%%%
\bibliographystyle{plainnat}
\bibliography{main}
%%%%%%%%%%%%%%%%%%%%%%



Version 0.9.1

1. 对图表caption新增了单行居中，多行左对齐。
2. 将reference的IEEE style去掉，改为plain，避免风险。
3. citation使用“[1]” ,而不是“ Li etal , 2025”, 和其他大厂模板对齐。


如何快速替换？

1. 替换bytedance_seed.cls文件为最新。
2. 将paper.tex里面
%%%%%%%%%%%%%%%%%%%%%%
\bibliographystyle{ieeenat_fullname}
\bibliography{main}
%%%%%%%%%%%%%%%%%%%%%%

换成
%%%%%%%%%%%%%%%%%%%%%%
\bibliographystyle{plain}
\bibliography{main}
%%%%%%%%%%%%%%%%%%%%%%