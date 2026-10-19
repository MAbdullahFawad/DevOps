import asyncio, traceback
from pathlib import Path
import nbformat
from nbclient import NotebookClient
project_dir = Path(__file__).resolve().parent
path = project_dir / 'TON_IoT_Research_Benchmark.ipynb'
nb=nbformat.read(path,as_version=4)
changes, nb=nbformat.validator.normalize(nb,version=4)
for cell in nb.cells:
    if cell.cell_type=='code':
        cell.setdefault('execution_count',None)
        cell.setdefault('outputs',[])
nbformat.validate(nb)
if changes:
    nbformat.write(nb,path)
client=NotebookClient(nb,timeout=3600,kernel_name='ton_iot_research',resources={'metadata':{'path':str(project_dir)}},allow_errors=False)
async def main():
    async with client.async_setup_kernel():
        try:
            for i,cell in enumerate(nb.cells):
                if cell.cell_type=='code':
                    print(f'RUNNING CELL {i+1}: {cell.source.splitlines()[0][:110]}',flush=True)
                    await client.async_execute_cell(cell,i)
                    nbformat.write(nb,path)
                    errors=[o for o in cell.get('outputs',[]) if o.output_type=='error']
                    if errors: print('CELL ERROR SAVED',errors[0].get('ename'),flush=True)
                else:
                    nbformat.write(nb,path)
        except BaseException:
            nbformat.write(nb,path)
            traceback.print_exc()
            raise
    print('NOTEBOOK EXECUTION COMPLETE',flush=True)
asyncio.run(main())

