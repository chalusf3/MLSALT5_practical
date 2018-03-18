import matplotlib.pyplot as plt
import numpy as np
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

systems = ['word.xml','word-sys2.xml','morph.xml']
xdata = np.array([1,2,3,4,5])
TWVs_single = [[0.446684,0.527085,0.343025,0.100000,0.000000],[0.455824,0.524442,0.340236,0.100000,0.000000],[0.525685,0.574665,0.293025,0,0.000000]]
TWVs_pairs = [[0.416860,0.493012,0.324892,0.097210,0.000000],[0.526613,0.591224,0.387446,0.097210,0.000000],[0.503382,0.573408,0.379076,0.097210,0.000000]]
TWVs_triple = [0.501239,0.565791,0.372102,0.094421,0.000000]

width = 0.15
plt.figure(0,figsize=(12,4))

ax = plt.subplot(121)
ax.bar(xdata - width, TWVs_single[0], width=width, color=(0,0,1,0.8), align='center', label=systems[0])
ax.bar(xdata,         TWVs_single[1], width=width, color=(0,1,0,0.8), align='center', label=systems[1])
ax.bar(xdata + width, TWVs_single[2], width=width, color=(1,0,0,0.8), align='center', label=systems[2])
ax.legend(loc = 'upper right')
# plt.xlim(min(xdata), max(xdata))
plt.ylim(0,.60)
plt.xlabel('Query length')
plt.ylabel('MTWV')
plt.title('MTWVs for different query lengths for single systems')
# plt.tight_layout()

width = 0.15
ax = plt.subplot(122)
ax.bar(xdata - 1.5*width, TWVs_pairs[0], width=width, color=(0,0,1,0.8), align='center', label='%s + %s' % (systems[0], systems[1]))
ax.bar(xdata - 0.5*width, TWVs_pairs[1], width=width, color=(0,1,0,0.8), align='center', label='%s + %s' % (systems[0], systems[2]))
ax.bar(xdata + 0.5*width, TWVs_pairs[2], width=width, color=(1,0,0,0.8), align='center', label='%s + %s' % (systems[1], systems[2]))
ax.bar(xdata + 1.5*width, TWVs_triple,   width=width, color=(1,1,0,0.8), align='center', label='%s + %s + %s' % (systems[0], systems[1], systems[2]))
ax.legend(loc = 'upper right')
plt.ylim(0,.60)
plt.xlabel('Query length')
plt.ylabel('MTWV')
plt.title('MTWVs for different query lengths for combined systems')
plt.savefig('q_length_MTWV', bbox_inches='tight')
plt.show()
# plt.clf()