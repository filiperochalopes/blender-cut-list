# (c) 2023 Filipe Lopes (@filiperochlopes) PT_BR 
# (c) 2022 Tim Huckaby (@timhuckaby)

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# ##### Versão PT_BR por Filipe Lopes #####
#
#  O código foi atualizado conforme proposto inicialmente por 
#  Tim Huckaby para bom funcionamento com o Cortecloud, muito utilizado
#  no Brasil para corte planejados, ficando esse plugin como uma opção
#  OpenSource para medidas de plano de corte
# 
# ##### Fim do Changelog #####

# Importando a API do blender
import bpy, os, re

# Configurações de ambiente para melhor uso em móveis e precisão
unit_settings = bpy.context.scene.unit_settings
unit_settings.system = 'METRIC'
unit_settings.scale_length = 0.001
unit_settings.length_unit = 'MILLIMETERS'
unit_settings.system_rotation = 'DEGREES'
# Cada cena é composta de várias áreas/janelas
areas = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
spaces = [s for s in areas if s.type == 'VIEW_3D']
workspace = None
for area in areas:
    for s in area.spaces:
        if s.type == 'VIEW_3D':
            s.shading.type = 'SOLID'
            s.shading.show_xray = True
            s.overlay.grid_scale = 0.001
            s.clip_end = 1000000
# Alterando o clipping point da camera ativa, caso exista uma
if bpy.context.scene.camera:
    bpy.context.scene.camera.data.clip_end = 1000000

# Atualizando para correção de medidas em script em relação ao viweport
bpy.context.view_layer.update()

# Captura apenas a seleção, gosto de utilizar coleções de madeira e outras de outros materiais, dessa forma fica fácil selecionar apenas os itens de madeira
selection = bpy.context.selected_objects

# Arquivo de saída (edite aqui)
output_file = 'Desktop/CutList.csv'
# string zerada para popular com dados csv
csv_output = ""
# lista de nome de objetos que não deverão ser analisados, pois são duplicatas de outros objetos. São esses os de final *.001, *.002 ...
blacklist = []

# classe para organizar a fitagem de borda de uma peça
class EdgeTapes:
    def __init__(self, material_names):
        def get_tape_material(tape_identifier:str):
            l = [m for m in material_names if tape_identifier in m]
            return l[0].replace(tape_identifier, '').strip() if len(l) > 0 else None
            
        # Verifica se existem algum material com as palavras chaves
        self.c1 = get_tape_material('C1')
        self.c2 = get_tape_material('C2')
        self.l1 = get_tape_material('L1')
        self.l2 = get_tape_material('L2')
    
    def __str__(self):
        str = ''
        if self.c1:
            str += f'C1: {self.c1} '
        if self.c2:
            str += f'C2: {self.c2} '
        if self.l1:
            str += f'L1: {self.l1} '
        if self.l2:
            str += f'L2: {self.l2} '
        return str
        
# classe para organizar as características de um corte do material
class WoodenPiece:
    def __init__(self, dimensions:list, material_names:list, name:str=None, comments:str=None):
        self.name = name
        self.comments = comments
        self.thickness = min(dimensions)
        dimensions.remove(self.thickness)
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.material = self.get_main_material_from_materials(material_names)
        self.edge_tapes = EdgeTapes(material_names)
    
    def get_main_material_from_materials(self, material_names):
        for m in material_names:
            if re.search("^((?!C1|C2|L1|L2|Fita).)*$", m):
                return f'{m} {self.thickness}mm'
        return None
    
    def __str__(self):
        return f'''
        Corte de MDF "{self.name}" - {self.comments} ({self.material})
        Dimensões (mm) {self.width}mm x {self.height}mm Espessura {self.thickness}mm
        Fitas: {self.edge_tapes}
        '''

# Cria o arquivo de saída no diretório "~/Desktop/CutList.csv"
user_folder = os.path.expanduser('~')
# make a filename
filename = os.path.join (user_folder, output_file)
# confirm path exists
os.makedirs(os.path.dirname(filename), exist_ok=True)
# open the file to write to
file = open(filename, "w")
# Escreve o cabeçalho do arquivo
file.write("Quantidade;Comprimento;Largura;Função;Fita C1;Fita C2;Fita L1;Fita L2;Material;Complemento\n")
# iterate through the selected objects
for sel in selection:
    if re.search(r"\.\d{3}$", sel.name):
        continue
    if sel.name not in blacklist:
        quantity = 1
        # captura o nome e as dimensões da peça selecionada
        wooden_piece = WoodenPiece(name=sel.name, dimensions=[int(sel.dimensions.x), int(sel.dimensions.y), int(sel.dimensions.z)], material_names=[m.name for m in sel.material_slots], comments=sel['comments'] if 'comments' in sel else None)
        # Verifica se temos outra peça com o mesmo nome e *.001 para adicionar na quantidade
        for s in selection:
            if(re.search(sel.name+r"\.\d{3}$", s.name)):
                blacklist.append(s.name)
                quantity += 1
        # Adiciona a linha ao csv
        file.write(f"{quantity};{wooden_piece.width};{wooden_piece.height};{wooden_piece.name};{wooden_piece.edge_tapes.c1 or ''};{wooden_piece.edge_tapes.c2 or ''};{wooden_piece.edge_tapes.l1 or ''};{wooden_piece.edge_tapes.l2 or ''};{wooden_piece.material};{wooden_piece.comments or ''}\n")

file.close()