from app import db, Table


Users = Table.Table(db, 'Users')
Projects = Table.Table(db, 'Projects')
Participants = Table.Table(db, 'Participants')
Commits = Table.Table(db, 'Commits')
Issues = Table.Table(db, 'Issues')
Changes = Table.Table(db, 'Changes')
Files = Table.Table(db, 'Commits')